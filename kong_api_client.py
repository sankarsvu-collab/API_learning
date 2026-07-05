import argparse
import json
import os
import requests
from requests.exceptions import RequestException


KONG_ADMIN_URL = os.getenv("KONG_ADMIN_URL", "http://localhost:8001").rstrip("/")
KONG_ADMIN_TOKEN = os.getenv("KONG_ADMIN_TOKEN", "")

HEADERS = {"Content-Type": "application/json"}
if KONG_ADMIN_TOKEN:
    HEADERS["Kong-Admin-Token"] = KONG_ADMIN_TOKEN


def request_json(method, path, payload=None):
    """Send a JSON request to the Kong Admin API."""
    url = f"{KONG_ADMIN_URL}{path}"
    response = requests.request(method, url, headers=HEADERS, json=payload, timeout=5)
    response.raise_for_status()
    return response.json() if response.content else {}


def list_services():
    """List all Kong services."""
    return request_json("GET", "/services")


def create_service(name, url):
    """Create a Kong service."""
    payload = {"name": name, "url": url}
    return request_json("POST", "/services", payload)


def list_routes():
    """List all Kong routes."""
    return request_json("GET", "/routes")


def create_route(service_name, path, route_name=None):
    """Create a route for an existing Kong service."""
    payload = {
        "name": route_name or f"{service_name}-route",
        "paths": [path],
        "service": {"name": service_name},
    }
    return request_json("POST", "/routes", payload)


def list_plugins():
    """List all Kong plugins."""
    return request_json("GET", "/plugins")


def create_plugin(plugin_name, config, service_name=None, route_name=None):
    """Create a plugin and optionally attach it to a service or route."""
    payload = {"name": plugin_name, "config": config}
    if service_name:
        payload["service"] = {"name": service_name}
    if route_name:
        payload["route"] = {"name": route_name}
    return request_json("POST", "/plugins", payload)


def main():
    parser = argparse.ArgumentParser(description="Simple Kong Admin API client")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="List resources")
    list_parser.add_argument("resource", choices=["services", "routes", "plugins"])

    create_service_parser = subparsers.add_parser("create-service", help="Create a service")
    create_service_parser.add_argument("name")
    create_service_parser.add_argument("url")

    create_route_parser = subparsers.add_parser("create-route", help="Create a route")
    create_route_parser.add_argument("service_name")
    create_route_parser.add_argument("path")
    create_route_parser.add_argument("route_name", nargs="?", default=None)

    create_plugin_parser = subparsers.add_parser("create-plugin", help="Create a plugin")
    create_plugin_parser.add_argument("plugin_name")
    create_plugin_parser.add_argument("config", help="Plugin config as JSON")
    create_plugin_parser.add_argument("--service", dest="service_name", default=None)
    create_plugin_parser.add_argument("--route", dest="route_name", default=None)

    args = parser.parse_args()

    print(f"Connecting to Kong Admin API at: {KONG_ADMIN_URL}")

    try:
        if args.command == "list":
            if args.resource == "services":
                print(json.dumps(list_services(), indent=2))
            elif args.resource == "routes":
                print(json.dumps(list_routes(), indent=2))
            else:
                print(json.dumps(list_plugins(), indent=2))
        elif args.command == "create-service":
            print(json.dumps(create_service(args.name, args.url), indent=2))
        elif args.command == "create-route":
            print(json.dumps(create_route(args.service_name, args.path, args.route_name), indent=2))
        elif args.command == "create-plugin":
            config = json.loads(args.config)
            print(json.dumps(create_plugin(args.plugin_name, config, args.service_name, args.route_name), indent=2))
        else:
            parser.print_help()
    except RequestException as exc:
        print(f"Request failed: {exc}")
        raise SystemExit(1)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON for plugin config: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
