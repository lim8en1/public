import angr, claripy, monkeyhex


# the possible password will be stored here
address = 0xDEAD0000
min_password_size = 4
max_password_size = 32
# hash value discovered on the remote target
target_hash = int.from_bytes(bytes.fromhex('<change-it>'.replace(' ', '')), 'little')

project = angr.Project('<path-to>/mysu.ko')

# getting some addresses to work with
write_addr = project.loader.main_object.get_symbol("dev_write")

# instruction address used on successful hash check
write_success_addr = write_addr.rebased_addr + 0x55
# instruction address used on hash check fail
write_failed_addr = write_addr.rebased_addr + 0x39
# address right before calling the hash function
write_addr_init = write_addr.rebased_addr + 0x2c
# users table address for a quick patch to use the target hash value instead of 0
users_table_addr = project.loader.main_object.get_symbol("users").rebased_addr

init_state = project.factory.entry_state(addr=write_addr_init)
# patching the 0-valued hash to the target hash value
init_state.mem[users_table_addr + 4].uint32_t = target_hash

# setting up the password address to be passed to the hash function as an argument
init_state.regs.rdi = address

for i in range(min_password_size, max_password_size):
    size = i
    # create the password variable and store it in the memory
    password = claripy.BVS('pwd', 8 * size)
    init_state.memory.store(address, password)
    init_state.mem[address + size].uint8_t = 0

    # try to find a possible solution
    simulation = project.factory.simgr(init_state)
    simulation.explore(find=write_success_addr, avoid=write_failed_addr)
    if simulation.found:
        # on success print the possible password value
        state = simulation.found[0]
        data = state.solver.eval(password, cast_to=bytes) + b'\0'
        print("Valid byte array discovered:")
        print(', '.join(f'0x{x:02x}' for x in data))
        exit(0)
print("Failed to find a valid password")
