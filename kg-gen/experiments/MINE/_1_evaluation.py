# # for running openie/graphrag evaluation on qwen
# from dotenv import load_dotenv
# import dspy
# from datasets import load_dataset
# from kg_gen.steps._3_deduplicate import DeduplicateMethod
# import numpy as np
# import networkx as nx
# from kg_gen.kg_gen import KGGen
# import json
# import sys
# import os
# from typing import Literal
# import typer
# from concurrent.futures import ThreadPoolExecutor, as_completed

# sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# load_dotenv()

# lm = dspy.LM(
#     model="ollama/qwen2.5:32b",
#     api_base="http://localhost:11434",
#     temperature=1.0,
#     max_tokens=16000,
# )
# dspy.configure(lm=lm)


# class EvaluateResponse(dspy.Signature):
#     """Determine whether the context contains the information stated in the correct answer. Respond with 1 if yes, 0 if no."""

#     context: str = dspy.InputField(desc="The context to evaluate")
#     correct_answer: str = dspy.InputField(desc="The correct answer to check for")
#     evaluation: int = dspy.OutputField(
#         desc="1 if context contains the correct answer, 0 otherwise"
#     )


# class ResponseEvaluator(dspy.Module):
#     def __init__(self):
#         super().__init__()
#         self.evaluate = dspy.ChainOfThought(EvaluateResponse)

#     def forward(self, context, correct_answer):
#         return self.evaluate(context=context, correct_answer=correct_answer)


# def gpt_evaluate_response(correct_answer: str, context: str) -> int:
#     evaluator = ResponseEvaluator()
#     result = evaluator.forward(context=context, correct_answer=correct_answer)
#     return result.evaluation


# def evaluate_accuracy(
#     kggen: KGGen,
#     queries: list[dict],
#     node_embeddings: dict[str, np.ndarray],
#     graph: nx.DiGraph,
#     output_file: str,
# ):
#     print(f"Graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")
#     correct = 0
#     results = []

#     for query in queries:
#         *_, context_text = kggen.retrieve(query, node_embeddings, graph)
#         evaluation = gpt_evaluate_response(query, context_text)
#         result = {
#             "correct_answer": query,
#             "retrieved_context": context_text,
#             "evaluation": evaluation,
#         }
#         results.append(result)
#         correct += evaluation

#     accuracy = correct / len(queries)
#     results.append({"accuracy": f"{accuracy * 100:.2f}%"})

#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(results, f, indent=2)
#     print(f"Results saved to {output_file}")


# def process_single_evaluation(
#     i: int,
#     data: dict | str,
#     queries: list[dict],
#     kggen: KGGen,
#     evaluation_model: str,
#     model_name: str,
#     reasoning_effort: str | None,
#     temperature: float,
#     deduplication_method: Literal["semhash", "full"] | None = "full",
#     no_dspy: bool = False,
# ) -> tuple[int, bool, str]:
#     """Process a single evaluation task. Returns (index, success, message)."""
#     if evaluation_model == "local":
#         dir_name = model_name.replace("/", "-")
#         if reasoning_effort:
#             dir_name += f"-{reasoning_effort}"
#         dir_name += f"-{temperature}"
#         if deduplication_method:
#             dir_name += f"-{deduplication_method}"
#         if no_dspy:
#             dir_name += "-no-dspy"
#     else:
#         dir_name = f"hf-{evaluation_model}"

#     output_file = f"results/{dir_name}/results_{i}.json"

#     # Skip if already completed successfully
#     if os.path.exists(output_file):
#         return (i, True, f"Already exists, skipping {output_file}")

#     try:
#         os.makedirs(os.path.dirname(output_file), exist_ok=True)

#         if not deduplication_method:
#             method = None
#         else:
#             method = (
#                 DeduplicateMethod.SEMHASH
#                 if deduplication_method == "semhash"
#                 else DeduplicateMethod.FULL
#             )

#         if evaluation_model == "local":
#             graph = kggen.generate(data, deduplication_method=method, no_dspy=no_dspy)
#             kg_output_file = f"results/{dir_name}/kg_{i}.json"
#             KGGen.export_graph(graph, kg_output_file)
#         else:
#             graph = kggen.from_dict(data)

#         nxGraph = kggen.to_nx(graph)
#         node_embeddings, _ = kggen.generate_embeddings(nxGraph)
#         evaluate_accuracy(kggen, queries, node_embeddings, nxGraph, output_file)
#         return (i, True, f"Successfully processed {output_file}")
#     except Exception as e:
#         return (i, False, f"Error processing {output_file}: {str(e)}")


# def _load_local(kg_file: str, queries_file: str, label: str):
#     """Load pre-built aligned KG and queries files."""
#     with open(kg_file, encoding="utf-8") as f:
#         kg_data = json.load(f)
#     with open(queries_file, encoding="utf-8") as f:
#         queries = json.load(f)
#     assert len(kg_data) == len(queries), (
#         f"[{label}] Alignment error: {len(kg_data)} KGs vs {len(queries)} query sets. "
#         f"Re-run the prepare script to regenerate both files."
#     )
#     print(f"[{label}] Loaded {len(kg_data)} aligned (KG, queries) pairs.")
#     return kg_data, queries


# def main(
#     model: str = "openai/gpt-5-nano",
#     api_key_env: str = "OPENAI_API_KEY",
#     api_base_url: str | None = None,
#     evaluation_model: Literal[
#         "local",
#         "kggen",        "kggen_local",
#         "graphrag",     "graphrag_local",
#         "openie",       "openie_local",
#         "mypipeline",
#     ] = "local",
#     reasoning_effort: str = None,
#     temperature: float = 1.0,
#     deduplication_method: Literal["semhash", "full"] | None = "semhash",
#     no_dspy: bool = False,
#     max_workers: int = 64,
# ):
#     # ── Local aligned files (bypasses HuggingFace) ────────
#     if evaluation_model == "kggen_local":
#         kg_data, queries = _load_local(
#             "kggen_pipeline_kgs.json", "kggen_queries.json", "kggen_local"
#         )
#     elif evaluation_model == "graphrag_local":
#         kg_data, queries = _load_local(
#             "graphrag_pipeline_kgs.json", "graphrag_queries.json", "graphrag_local"
#         )
#     elif evaluation_model == "openie_local":
#         kg_data, queries = _load_local(
#             "openie_pipeline_kgs.json", "openie_queries.json", "openie_local"
#         )

#     # ── HuggingFace / other modes ─────────────────────────
#     else:
#         dataset = load_dataset("josancamon/kg-gen-MINE-evaluation-dataset")["train"]
#         queries = [item["generated_queries"] for item in dataset.to_list()]

#         if evaluation_model == "local":
#             kg_data = [item["essay_content"] for item in dataset.to_list()]
#         elif evaluation_model == "kggen":
#             kg_data = [item["kggen"] for item in dataset.to_list()]
#         elif evaluation_model == "graphrag":
#             kg_data = [item["graphrag_kg"] for item in dataset.to_list()]
#         elif evaluation_model == "openie":
#             kg_data = [item["openie_kg"] for item in dataset.to_list()]
#         elif evaluation_model == "mypipeline":
#             with open("my_pipeline_kgs.json") as f:
#                 kg_data = json.load(f)

#     kggen_instance = KGGen(
#         retrieval_model="all-MiniLM-L6-v2",
#         reasoning_effort=reasoning_effort,
#         temperature=temperature,
#         model=model,
#         api_key=os.getenv(api_key_env),
#         api_base=api_base_url,
#         max_tokens=64000,
#     )

#     valid_pairs = [(kg, q) for kg, q in zip(kg_data, queries) if kg is not None]
#     print(f"Processing {len(valid_pairs)} evaluations with {max_workers} workers...")

#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         futures = {
#             executor.submit(
#                 process_single_evaluation,
#                 i, kg, q, kggen_instance,
#                 evaluation_model, model, reasoning_effort,
#                 temperature, deduplication_method, no_dspy,
#             ): i
#             for i, (kg, q) in enumerate(valid_pairs)
#         }

#         completed = 0
#         for future in as_completed(futures):
#             completed += 1
#             i, success, message = future.result()
#             status = "✓" if success else "✗"
#             print(f"[{completed}/{len(valid_pairs)}] {status} {message}")

#     print(f"\nCompleted all {len(valid_pairs)} evaluations!")


# if __name__ == "__main__":
#     typer.run(main)
#     # Example runs:
#     # python evaluation.py --evaluation-model kggen_local
#     # python evaluation.py --evaluation-model graphrag_local
#     # python evaluation.py --evaluation-model openie_local
#     # python evaluation.py --evaluation-model mypipeline
































# for running mypipeline evaluation on qwen 

from dotenv import load_dotenv
import dspy
from datasets import load_dataset
from kg_gen.steps._3_deduplicate import DeduplicateMethod
import numpy as np
import networkx as nx
from kg_gen.kg_gen import KGGen
import json
import sys
import os
from typing import Literal
import typer
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the src directory to Python path to import from source code
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

load_dotenv()

# Configure DSPy with OpenAI
# lm = dspy.LM(
#     model="openai/gpt-5",
#     api_key=os.getenv("OPENAI_API_KEY"),
#     reasoning_effort="high",
#     temperature=1.0,
#     max_tokens=16000,
# )
# dspy.configure(lm=lm)
lm = dspy.LM(
    model="ollama/qwen2.5:32b",  # your ollama model name
    api_base="http://localhost:11434",
    temperature=1.0,
    max_tokens=16000,
)
dspy.configure(lm=lm)

# Define DSPy signature for evaluation
class EvaluateResponse(dspy.Signature):
    """Determine whether the context contains the information stated in the correct answer. Respond with 1 if yes, 0 if no."""

    context: str = dspy.InputField(desc="The context to evaluate")
    correct_answer: str = dspy.InputField(desc="The correct answer to check for")
    evaluation: int = dspy.OutputField(
        desc="1 if context contains the correct answer, 0 otherwise"
    )


# Create DSPy module for evaluation
class ResponseEvaluator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.evaluate = dspy.ChainOfThought(EvaluateResponse)

    def forward(self, context, correct_answer):
        return self.evaluate(context=context, correct_answer=correct_answer)


def gpt_evaluate_response(correct_answer: str, context: str) -> int:
    evaluator = ResponseEvaluator()
    result = evaluator.forward(context=context, correct_answer=correct_answer)
    return result.evaluation


def evaluate_accuracy(
    kggen: KGGen,
    queries: list[dict],
    node_embeddings: dict[str, np.ndarray],
    graph: nx.DiGraph,
    output_file: str,
):
    print(
        f"Graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges."
    )
    correct = 0
    results = []

    for query in queries:
        *_, context_text = kggen.retrieve(query, node_embeddings, graph)
        evaluation = gpt_evaluate_response(query, context_text)
        result = {
            "correct_answer": query,
            "retrieved_context": context_text,
            "evaluation": evaluation,
        }
        results.append(result)
        correct += evaluation

    accuracy = correct / len(queries)
    results.append({"accuracy": f"{accuracy * 100:.2f}%"})

    # Save results to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_file}")


def process_single_evaluation(
    i: int,
    data: dict | str,
    queries: list[dict],
    kggen: KGGen,
    evaluation_model: str,
    model_name: str,
    reasoning_effort: str | None,
    temperature: float,
    deduplication_method: Literal["semhash", "full"] | None = "full",
    no_dspy: bool = False,
) -> tuple[int, bool, str]:
    """Process a single evaluation task. Returns (index, success, message)."""
    # Build directory name based on evaluation model
    if evaluation_model == "local":
        # Build directory name from model config
        dir_name = model_name.replace("/", "-")
        if reasoning_effort:
            dir_name += f"-{reasoning_effort}"
        dir_name += f"-{temperature}"
        if deduplication_method:
            dir_name += f"-{deduplication_method}"
        if no_dspy:
            dir_name += "-no-dspy"
    else:
        # For pre-generated KGs from HuggingFace dataset
        dir_name = f"hf-{evaluation_model}"

    # output_file = f"experiments/MINE/results/{dir_name}/results_{i}.json"
    output_file = f"results/{dir_name}/results_{i}.json"
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        if not deduplication_method:
            method = None
        else:
            method = (
                DeduplicateMethod.SEMHASH
                if deduplication_method == "semhash"
                else DeduplicateMethod.FULL
            )

        if evaluation_model == "local":
            # Generate the graph from text
            graph = kggen.generate(data, deduplication_method=method, no_dspy=no_dspy)
            # kg_output_file = f"experiments/MINE/results/{dir_name}/kg_{i}.json"
            kg_output_file = f"results/{dir_name}/kg_{i}.json"
            KGGen.export_graph(graph, kg_output_file)
        else:
            graph = kggen.from_dict(data)

        nxGraph = kggen.to_nx(graph)
        node_embeddings, _ = kggen.generate_embeddings(nxGraph)
        evaluate_accuracy(
            kggen,
            queries,
            node_embeddings,
            nxGraph,
            output_file,
        )
        return (i, True, f"Successfully processed {output_file}")
    except Exception as e:
        return (i, False, f"Error processing {output_file}: {str(e)}")


def main(
    model: str = "openai/gpt-5-nano",
    api_key_env: str = "OPENAI_API_KEY",
    api_base_url: str | None = None,
    # local: means re-run the KG generation step
    # kggen: means use the KG generated and saved in the huggingface dataset, same for graphrag and openie
    evaluation_model: Literal["local", "kggen", "graphrag", "openie","mypipeline"] = "local",
    reasoning_effort: str = None,
    temperature: float = 1.0,
    deduplication_method: Literal["semhash", "full"] | None = "semhash",
    no_dspy: bool = False,
    max_workers: int = 64,
):
    # Load data from Hugging Face (with local fallback)
    dataset = load_dataset("josancamon/kg-gen-MINE-evaluation-dataset")["train"]
    queries = [item["generated_queries"] for item in dataset.to_list()]

    if evaluation_model == "local":
        kg_data = [item["essay_content"] for item in dataset.to_list()]
    elif evaluation_model == "kggen":
        kg_data = [item["kggen"] for item in dataset.to_list()]
    elif evaluation_model == "graphrag":
        kg_data = [item["graphrag_kg"] for item in dataset.to_list()]
    elif evaluation_model == "openie":
        kg_data = [item["openie_kg"] for item in dataset.to_list()]
    elif evaluation_model == "mypipeline":
        with open("my_pipeline_kgs.json") as f:
            kg_data = json.load(f)

    kggen = KGGen(
        retrieval_model="all-MiniLM-L6-v2",
        reasoning_effort=reasoning_effort,
        temperature=temperature,
        model=model,
        api_key=os.getenv(api_key_env),
        api_base=api_base_url,
        max_tokens=64000,
    )
    valid_pairs = [
        (kg, queries) for kg, queries in zip(kg_data, queries) if kg is not None
    ]

    print(f"Processing {len(valid_pairs)} evaluations with {max_workers} workers...")

    # Process evaluations in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(
                process_single_evaluation,
                i,
                kg,
                queries,
                kggen,
                evaluation_model,
                model,
                reasoning_effort,
                temperature,
                deduplication_method,
                no_dspy,
            ): i
            for i, (kg, queries) in enumerate(valid_pairs)
        }

        # Process results as they complete
        completed = 0
        for future in as_completed(futures):
            completed += 1
            i, success, message = future.result()
            status = "✓" if success else "✗"
            print(f"[{completed}/{len(valid_pairs)}] {status} {message}")

    print(f"\nCompleted all {len(valid_pairs)} evaluations!")


if __name__ == "__main__":
    typer.run(main)
    # uv run experiments/MINE/_1_evaluation.py --model together_ai/openai/gpt-oss-20b --reasoning-effort low --deduplication-method semhash --max-workers 110 --api-base-url https://api.together.xyz/v1 --api-key-env TOGETHER_API_KEY








# for running kggen evaluation on qwen

# from dotenv import load_dotenv
# import dspy
# from datasets import load_dataset
# from kg_gen.steps._3_deduplicate import DeduplicateMethod
# import numpy as np
# import networkx as nx
# from kg_gen.kg_gen import KGGen
# import json
# import sys
# import os
# from typing import Literal
# import typer
# from concurrent.futures import ThreadPoolExecutor, as_completed

# sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# load_dotenv()

# lm = dspy.LM(
#     model="ollama/qwen2.5:32b",
#     api_base="http://localhost:11434",
#     temperature=1.0,
#     max_tokens=16000,
# )
# dspy.configure(lm=lm)


# class EvaluateResponse(dspy.Signature):
#     """Determine whether the context contains the information stated in the correct answer. Respond with 1 if yes, 0 if no."""

#     context: str = dspy.InputField(desc="The context to evaluate")
#     correct_answer: str = dspy.InputField(desc="The correct answer to check for")
#     evaluation: int = dspy.OutputField(
#         desc="1 if context contains the correct answer, 0 otherwise"
#     )


# class ResponseEvaluator(dspy.Module):
#     def __init__(self):
#         super().__init__()
#         self.evaluate = dspy.ChainOfThought(EvaluateResponse)

#     def forward(self, context, correct_answer):
#         return self.evaluate(context=context, correct_answer=correct_answer)


# def gpt_evaluate_response(correct_answer: str, context: str) -> int:
#     evaluator = ResponseEvaluator()
#     result = evaluator.forward(context=context, correct_answer=correct_answer)
#     return result.evaluation


# def evaluate_accuracy(
#     kggen: KGGen,
#     queries: list[dict],
#     node_embeddings: dict[str, np.ndarray],
#     graph: nx.DiGraph,
#     output_file: str,
# ):
#     print(
#         f"Graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges."
#     )
#     correct = 0
#     results = []

#     for query in queries:
#         *_, context_text = kggen.retrieve(query, node_embeddings, graph)
#         evaluation = gpt_evaluate_response(query, context_text)
#         result = {
#             "correct_answer": query,
#             "retrieved_context": context_text,
#             "evaluation": evaluation,
#         }
#         results.append(result)
#         correct += evaluation

#     accuracy = correct / len(queries)
#     results.append({"accuracy": f"{accuracy * 100:.2f}%"})

#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(results, f, indent=2)
#     print(f"Results saved to {output_file}")


# def process_single_evaluation(
#     i: int,
#     data: dict | str,
#     queries: list[dict],
#     kggen: KGGen,
#     evaluation_model: str,
#     model_name: str,
#     reasoning_effort: str | None,
#     temperature: float,
#     deduplication_method: Literal["semhash", "full"] | None = "full",
#     no_dspy: bool = False,
# ) -> tuple[int, bool, str]:
#     """Process a single evaluation task. Returns (index, success, message)."""
#     if evaluation_model == "local":
#         dir_name = model_name.replace("/", "-")
#         if reasoning_effort:
#             dir_name += f"-{reasoning_effort}"
#         dir_name += f"-{temperature}"
#         if deduplication_method:
#             dir_name += f"-{deduplication_method}"
#         if no_dspy:
#             dir_name += "-no-dspy"
#     else:
#         dir_name = f"hf-{evaluation_model}"

#     output_file = f"results/{dir_name}/results_{i}.json"
#     try:
#         os.makedirs(os.path.dirname(output_file), exist_ok=True)

#         if not deduplication_method:
#             method = None
#         else:
#             method = (
#                 DeduplicateMethod.SEMHASH
#                 if deduplication_method == "semhash"
#                 else DeduplicateMethod.FULL
#             )

#         if evaluation_model == "local":
#             graph = kggen.generate(data, deduplication_method=method, no_dspy=no_dspy)
#             kg_output_file = f"results/{dir_name}/kg_{i}.json"
#             KGGen.export_graph(graph, kg_output_file)
#         else:
#             graph = kggen.from_dict(data)

#         nxGraph = kggen.to_nx(graph)
#         node_embeddings, _ = kggen.generate_embeddings(nxGraph)
#         evaluate_accuracy(
#             kggen,
#             queries,
#             node_embeddings,
#             nxGraph,
#             output_file,
#         )
#         return (i, True, f"Successfully processed {output_file}")
#     except Exception as e:
#         return (i, False, f"Error processing {output_file}: {str(e)}")


# def main(
#     model: str = "openai/gpt-5-nano",
#     api_key_env: str = "OPENAI_API_KEY",
#     api_base_url: str | None = None,
#     evaluation_model: Literal[
#         "local", "kggen", "graphrag", "openie", "mypipeline", "kggen_local"
#     ] = "local",
#     reasoning_effort: str = None,
#     temperature: float = 1.0,
#     deduplication_method: Literal["semhash", "full"] | None = "semhash",
#     no_dspy: bool = False,
#     max_workers: int = 64,
# ):
#     # ------------------------------------------------------------------ #
#     #  kggen_local: load pre-built aligned files instead of HuggingFace  #
#     # ------------------------------------------------------------------ #
#     if evaluation_model == "kggen_local":
#         with open("kggen_pipeline_kgs.json", encoding="utf-8") as f:
#             kg_data = json.load(f)
#         with open("kggen_queries.json", encoding="utf-8") as f:
#             queries = json.load(f)

#         # Sanity check — must be aligned
#         assert len(kg_data) == len(queries), (
#             f"Alignment error: {len(kg_data)} KGs vs {len(queries)} query sets. "
#             "Re-run prepare_kggen_eval.py to regenerate both files."
#         )
#         print(f"Loaded {len(kg_data)} aligned (KG, queries) pairs from local files.")

#     else:
#         # ------------------------------------------------------------------ #
#         #  All other modes: pull from HuggingFace as before                  #
#         # ------------------------------------------------------------------ #
#         dataset = load_dataset("josancamon/kg-gen-MINE-evaluation-dataset")["train"]
#         queries = [item["generated_queries"] for item in dataset.to_list()]

#         if evaluation_model == "local":
#             kg_data = [item["essay_content"] for item in dataset.to_list()]
#         elif evaluation_model == "kggen":
#             kg_data = [item["kggen"] for item in dataset.to_list()]
#         elif evaluation_model == "graphrag":
#             kg_data = [item["graphrag_kg"] for item in dataset.to_list()]
#         elif evaluation_model == "openie":
#             kg_data = [item["openie_kg"] for item in dataset.to_list()]
#         elif evaluation_model == "mypipeline":
#             with open("my_pipeline_kgs.json") as f:
#                 kg_data = json.load(f)

#     kggen_instance = KGGen(
#         retrieval_model="all-MiniLM-L6-v2",
#         reasoning_effort=reasoning_effort,
#         temperature=temperature,
#         model=model,
#         api_key=os.getenv(api_key_env),
#         api_base=api_base_url,
#         max_tokens=64000,
#     )

#     valid_pairs = [
#         (kg, q) for kg, q in zip(kg_data, queries) if kg is not None
#     ]

#     print(f"Processing {len(valid_pairs)} evaluations with {max_workers} workers...")

#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         futures = {
#             executor.submit(
#                 process_single_evaluation,
#                 i,
#                 kg,
#                 q,
#                 kggen_instance,
#                 evaluation_model,
#                 model,
#                 reasoning_effort,
#                 temperature,
#                 deduplication_method,
#                 no_dspy,
#             ): i
#             for i, (kg, q) in enumerate(valid_pairs)
#         }

#         completed = 0
#         for future in as_completed(futures):
#             completed += 1
#             i, success, message = future.result()
#             status = "✓" if success else "✗"
#             print(f"[{completed}/{len(valid_pairs)}] {status} {message}")

#     print(f"\nCompleted all {len(valid_pairs)} evaluations!")


# if __name__ == "__main__":
#     typer.run(main)
#     # Example run:
#     # uv run evaluation.py --evaluation-model kggen_local


