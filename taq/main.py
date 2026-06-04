import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="TaQ Engine - Tactical Analysis & Qualification Engine")
    parser.add_argument("--config", "-c", type=str, help="Path to config YAML")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host")
    parser.add_argument("--port", type=int, default=8400, help="Port")
    parser.add_argument("--reload", action="store_true", help="Auto-reload")
    args = parser.parse_args()
    if args.config:
        from taq.core.config import load_config
        load_config(args.config)
    uvicorn.run("taq.api.server:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
