
import requests

def main():
    print("Hello from hello!")
    print(requests.get('https://httpbin.org/get').status_code)

if __name__ == "__main__":
    main()
