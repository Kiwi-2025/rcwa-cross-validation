from argparse import ArgumentParser
from contextlib import ExitStack
from pathlib import Path
import json

import yaml

from .case_loader import ROOT, catalog, load_case, points, resolve
from .reporting.tables import compare_run, generate_report, publish_benchmark, update_categories
from .runner import configure, import_lumerical, run
from .solvers import MODULES, adapter
from .validation.convergence import settings_series


def parser():
    cli = ArgumentParser(prog="rcwa-cv")
    commands = cli.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    commands.add_parser("list")
    benchmark = commands.add_parser("benchmark", help="Run every case and refresh the README and case figures.")
    benchmark.add_argument("--profile", choices=["quick","pilot","convergence"], default="quick")
    benchmark.set_defaults(selection="all", solvers=",".join(MODULES),
                           point_limit=None, representative=False, resume=None)
    for name in ("run", "converge"):
        cmd = commands.add_parser(name)
        cmd.add_argument("selection", help="Case ID, category, or all.")
        cmd.add_argument("--solvers","--solver", default=",".join(MODULES))
        cmd.add_argument("--profile", choices=["quick","pilot","convergence"],
                         default="quick" if name=="run" else "convergence")
        cmd.add_argument("--resume", help="Retry unfinished solvers in a saved run with the same arguments.")
        limits = cmd.add_mutually_exclusive_group()
        limits.add_argument("--point-limit", type=int)
        limits.add_argument("--representative", action="store_true")
    for name in ("compare","report"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--run", required=True, help="Run ID or directory.")
    export = commands.add_parser("export-lumerical")
    export.add_argument("selection")
    export.add_argument("--profile", choices=["quick","pilot","convergence"], default="quick")
    export.add_argument("--point", type=int, default=0)
    imported = commands.add_parser("import-lumerical")
    imported.add_argument("--run", required=True)
    imported.add_argument("--point", type=int, required=True)
    imported.add_argument("--mat", type=Path, required=True)
    return cli


def find_run(run, cli):
    directory = Path(run)
    if (directory/"manifest.json").is_file():
        return directory
    matches = list((ROOT/"results").glob(f"*/*/{run}/manifest.json"))
    if len(matches) != 1:
        cli.error("Run ID did not resolve to exactly one saved run.")
    return matches[0].parent


def main():
    cli = parser()
    args = cli.parse_args()
    configure()
    if args.command=="doctor":
        for name in MODULES:
            try:
                print(name, json.dumps(adapter(name).probe()))
            except Exception as exc:
                print(f"{name}: unavailable ({exc})")
        return
    if args.command=="list":
        for p in catalog():
            case = load_case(p)
            print(f"{case['id']}  {case['title']}")
        return
    if args.command in ("compare","report","import-lumerical"):
        directory = find_run(args.run, cli)
        if args.command == "import-lumerical":
            if not args.mat.is_file():
                cli.error("The Lumerical MAT file does not exist.")
            import_lumerical(directory, args.point, args.mat)
        summary = compare_run(directory)[0] if args.command=="compare" else generate_report(directory)
        update_categories()
        print(f"{directory} [{summary['status']}]")
        return
    if args.command=="export-lumerical":
        from .solvers.lumerical import build_script
        profile = yaml.safe_load((ROOT/f"configs/{args.profile}.yaml").read_text(encoding="utf-8"))
        for p in catalog(args.selection):
            case = load_case(p)
            samples = list(points(case,args.profile))
            if not 0 <= args.point < len(samples):
                cli.error(f"Point index out of range for {case['id']}.")
            variant, overrides = samples[args.point]
            _, settings = settings_series(case,profile,"lumerical")[0]
            resolved = resolve(case,variant,overrides,settings)
            output = ROOT/"results"/case["id"][0]/case["id"]/"lumerical_exports"
            output.mkdir(exist_ok=True,parents=True)
            path = output/f"{args.profile}-{args.point:04d}.lsf"
            path.write_text(build_script(resolved,settings,"rcwa_output.mat"),encoding="utf-8")
            print(path)
        return
    solvers = list(dict.fromkeys(x.strip() for x in args.solvers.split(",") if x.strip()))
    if not solvers or set(solvers).difference(MODULES):
        cli.error(f"Choose solvers from {', '.join(MODULES)}.")
    if args.point_limit is not None and args.point_limit <= 0:
        cli.error("--point-limit must be positive.")
    selected = catalog(args.selection)
    resume = find_run(args.resume, cli) if args.resume else None
    if resume is not None and len(selected) != 1:
        cli.error("Resume applies to a single case.")
    folders = []
    complete = True
    with ExitStack() as stack:
        if "lumerical" in solvers and len(selected) > 1:
            try:
                stack.enter_context(adapter("lumerical").session())
            except Exception as exc:
                print(f"Lumerical session initialization: {exc}", flush=True)
        for p in selected:
            folder = run(p, solvers, args.profile, args.point_limit, args.representative, resume)
            result = generate_report(folder)
            folders.append(folder)
            complete &= all(result["solvers"].get(name)=="COMPLETE" for name in MODULES)
            print(f"{folder} [{result['status']}]", flush=True)
    if args.command=="benchmark":
        if not complete:
            cli.exit(1, "Benchmark incomplete. See the per-case manifests. The README snapshot is unchanged.\n")
        update_categories(folders)
        publish_benchmark(folders)
    else:
        update_categories()


if __name__=="__main__":
    main()
