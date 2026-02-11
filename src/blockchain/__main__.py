import argparse

import uvicorn

from .node import Node, create_app


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--complexity", type=int, default=3)
    args = p.parse_args()

    node = Node(complexity=args.complexity)
    app = create_app(node)

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
