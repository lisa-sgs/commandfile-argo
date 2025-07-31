import json
import logging
import os
from argparse import ArgumentParser
from pathlib import Path

from commandfile.io import write_cmdfile_yaml
from commandfile.model import Commandfile, Filelist, Parameter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_args():
    parser = ArgumentParser(
        description="Generate a commandfile from Argo workflow environment."
    )
    parser.add_argument("output", type=Path, help="Path to the output commandfile.")
    return parser.parse_args()


def generate_commandfile(output_file: Path):
    try:
        template_contents = os.environ["ARGO_TEMPLATE"]
    except KeyError:
        raise ValueError("Environment variable 'ARGO_TEMPLATE' is not set.")

    try:
        parameters_contents = os.environ["INPUTS_PARAMETERS"]
    except KeyError:
        raise ValueError("Environment variable 'INPUTS_PARAMETERS' is not set.")

    logger.info("ARGO_TEMPLATE: %s", template_contents)
    logger.info("INPUTS_PARAMETERS: %s", parameters_contents)

    argo_template = json.loads(template_contents)
    argo_parameters = json.loads(parameters_contents)
    params, input_files = transform_complex_parameters(argo_parameters)

    commandfile = Commandfile(
        header={},
        parameters=params,
        inputs=[
            Filelist(key=a["name"], files=[a["path"]])
            for a in argo_template["inputs"].get("artifacts", [])
        ]
        + input_files,
        outputs=[
            Filelist(key=a["name"], files=[a["path"]])
            for a in argo_template["outputs"].get("artifacts", [])
        ],
    )
    write_cmdfile_yaml(commandfile, output_file)
    logger.info(
        "Written command file to %s:\n%s",
        output_file,
        commandfile.model_dump_json(),
    )


def transform_complex_parameters(
    params: list,
) -> tuple[list[Parameter], list[Filelist]]:
    parameters = []
    input_files = []
    for param in params:
        try:
            # Parameters containing JSON arrays are implicitly transformed to input
            # filelists.
            content = json.loads(param["value"])
            if isinstance(content, list) and all(
                isinstance(item, str) for item in content
            ):
                input_files.append(Filelist(key=param["name"], files=content))
                continue
        except json.JSONDecodeError:
            pass

        # For other parameters, we keep them as-is.
        parameters.append(Parameter(key=param["name"], value=param["value"]))

    return parameters, input_files


def main():
    args = get_args()
    generate_commandfile(args.output)
