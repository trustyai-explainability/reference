import argparse
from caikit_nlp.modules.text_classification import SequenceClassification

def _parse_args():
    parser = argparse.ArgumentParser(
        description=""
    )
    parser.add_argument(
        "-m", "--model_id", required=True, help="Model name or path"
    )
    parser.add_argument(
        "-o", "--output_model_dir", required=True, help="Output model directory"
    )


    args = parser.parse_args()
    return args.model_id, args.output_model_dir

if __name__ == "__main__":
    model_id, output_model_dir = _parse_args()
    print("MODEL NAME OR PATH: ", model_id)
    print("OUTPUT PATH: ", output_model_dir)
    SequenceClassification.bootstrap(model_id).save(output_model_dir)