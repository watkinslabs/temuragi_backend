import argparse
from .agent import TemuragiModuleAgent

def main():
    p = argparse.ArgumentParser(prog="temuragi-agent")
    sp = p.add_subparsers(dest="cmd", required=True)

    sp.add_parser("discover", help="build spec.yaml")
    sp.add_parser("confirm", help="confirm spec.yaml before generation")

    gen = sp.add_parser("generate", help="generate one step")
    gen.add_argument("step", choices=["model","service","route","hook"])
    
    sp.add_parser("generate_all", help="run all generate steps in order")

    args = p.parse_args()
    agent = TemuragiModuleAgent()

    if args.cmd == "discover":
        agent.discover()
    elif args.cmd == "confirm":
        agent.confirm()
    elif args.cmd == "generate":
        agent.generate_step(args.step)
    elif args.cmd == "generate_all":
        agent.generate_all()

if __name__ == "__main__":
    main()
