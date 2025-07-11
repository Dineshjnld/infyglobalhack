# AgriGuru - Crop NLP Insights Generator Module
# Generates textual planting advice using Hugging Face Transformers based on ML model predictions.

import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch

from config import settings # For potential model path configurations or HF cache dir

# --- Model Configuration ---
# Using a smaller T5 model for faster loading and inference, suitable for CPU.
# If a GPU is available and configured with PyTorch, it might be used automatically by pipeline.
# The brief mentions "Fine-tune BERT or T5 (Hugging Face) with RAG".
# For this initial implementation, we'll use a pre-trained T5 for text generation
# based on structured input, which is a form of simplified, prompt-based "Retrieval-Augmented Generation"
# where the "retrieved" context is the output of our ML model.
# Full RAG would involve a vector DB and more complex context retrieval, which is out of scope for this step.

# Define a cache directory for Hugging Face models if needed, to be set via .env
# HF_MODEL_CACHE = getattr(settings, 'HF_MODEL_CACHE_DIR', None) # Example from .env.example
HF_MODEL_CACHE = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data', 'models', 'hf_cache'))
os.makedirs(HF_MODEL_CACHE, exist_ok=True)

# Using a smaller, general-purpose T5 model.
# Larger or fine-tuned models would provide better, more specific advice.
# MODEL_NAME = "t5-small"
# For potentially better quality and still manageable size:
MODEL_NAME = "google/flan-t5-small" # FLAN-T5 models are generally good at instruction following

# Global variables for model and tokenizer to load them only once.
nlp_model = None
nlp_tokenizer = None
text_generator_pipeline = None

def load_nlp_model_and_tokenizer(model_name=MODEL_NAME, cache_dir=HF_MODEL_CACHE):
    """Loads the NLP model and tokenizer from Hugging Face Transformers."""
    global nlp_model, nlp_tokenizer, text_generator_pipeline

    if text_generator_pipeline is None: # Check pipeline as it's the end goal
        try:
            print(f"INFO: Loading NLP model and tokenizer: {model_name} from Hugging Face Hub (or cache: {cache_dir})...")
            # For Seq2Seq models like T5 for text generation tasks.
            # nlp_tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
            # nlp_model = AutoModelForSeq2SeqLM.from_pretrained(model_name, cache_dir=cache_dir)

            # Using pipeline for easier text generation
            # For summarization or text generation, "text2text-generation" is suitable for T5
            # For models like GPT-2/BERT for generation, "text-generation" might be used.
            device = 0 if torch.cuda.is_available() and torch.cuda.device_count() > 0 else -1 # Use GPU if available
            print(f"INFO: Using device: {'cuda' if device == 0 else 'cpu'} for NLP model.")

            text_generator_pipeline = pipeline(
                "text2text-generation",
                model=model_name,
                tokenizer=model_name, # Pipeline can also take model_name for tokenizer
                cache_dir=cache_dir,
                device=device,
                max_length=100, # Max length of generated advice
                min_length=10   # Min length
            )
            print(f"INFO: NLP model {model_name} loaded successfully using pipeline.")
        except Exception as e:
            print(f"ERROR: Could not load NLP model or tokenizer '{model_name}': {e}")
            print("NLP insights will be very basic or unavailable.")
            # Fallback to ensure nlp_model and nlp_tokenizer are not None if pipeline fails early
            nlp_model = None
            nlp_tokenizer = None
            text_generator_pipeline = None # Ensure it's None on failure
    return text_generator_pipeline


def generate_planting_advice(crop_suitability_predictions):
    """
    Generates textual planting advice for recommended crops using a pre-trained LLM.

    Args:
        crop_suitability_predictions (list of dict): A list of dictionaries, where each dict
            contains 'predicted_crop' (str) and 'suitability_scores' (dict of crop: "prob%").
            Example: [{'predicted_crop': 'Wheat', 'suitability_scores': {'Wheat': '90.50%', 'Rice': '8.00%'}}]

    Returns:
        list of dict: List of dictionaries, each containing the crop, its top score, and generated advice.
                      Example: [{'crop': 'Wheat', 'suitability': '90.50%', 'advice': 'Consider planting Wheat...'}, ...]
    """
    generator = load_nlp_model_and_tokenizer()
    if not generator:
        # Fallback if model loading failed
        advice_list = []
        for prediction in crop_suitability_predictions:
            crop_name = prediction.get('predicted_crop', 'Unknown Crop')
            # Get the suitability score for the predicted_crop itself
            top_score = prediction.get('suitability_scores', {}).get(crop_name, "N/A")
            advice_list.append({
                "crop": crop_name,
                "suitability": top_score,
                "advice": f"Basic advice for {crop_name}: Ensure proper soil preparation and water management. (NLP model not available for detailed advice)"
            })
        return advice_list

    generated_advices = []
    print(f"INFO: Generating advice for {len(crop_suitability_predictions)} prediction(s).")

    for prediction in crop_suitability_predictions:
        crop_name = prediction.get('predicted_crop')
        if not crop_name:
            continue

        # Get the suitability score for the predicted_crop itself
        suitability_score_str = prediction.get('suitability_scores', {}).get(crop_name, "a good")
        # Remove '%' if present for cleaner prompt
        suitability_score_val = suitability_score_str.replace('%', '')

        # Construct a prompt for the T5 model
        # T5 models often work well with task prefixes.
        # Prompt engineering is key here for good results.
        prompt = (
            f"Generate concise planting advice for a farmer in India considering planting {crop_name}. "
            f"This crop has a suitability score of {suitability_score_val}%. "
            f"Focus on key actions like ideal planting time (general season), soil preparation, and initial watering needs. "
            f"Keep the advice short and practical, in one or two sentences."
        )

        # print(f"DEBUG: NLP Prompt for {crop_name}: {prompt}")

        try:
            # The pipeline handles tokenization and decoding.
            # For T5, max_length in pipeline setup is important.
            outputs = generator(prompt, num_beams=4, no_repeat_ngram_size=2, early_stopping=True)
            advice_text = outputs[0]['generated_text'] if outputs and outputs[0]['generated_text'] else f"No specific advice generated for {crop_name}."
        except Exception as e:
            print(f"ERROR: Failed to generate advice for {crop_name} with NLP model: {e}")
            advice_text = f"Could not generate detailed advice for {crop_name} due to an error. General advice: follow local best practices."

        generated_advices.append({
            "crop": crop_name,
            "suitability": suitability_score_str, # The original string with '%'
            "advice": advice_text.strip()
        })

    return generated_advices


if __name__ == '__main__':
    print("--- Testing Crop NLP Generator ---")

    # Ensure model is downloaded/cached first if running standalone
    print("Attempting to load NLP model (may take time on first run)...")
    pipeline_instance = load_nlp_model_and_tokenizer()
    if not pipeline_instance:
        print("NLP model could not be loaded. Exiting test.")
    else:
        print("NLP model loaded. Proceeding with tests.")

        # Example 1: Single crop prediction
        print("\n--- Test 1: Single Crop Prediction ---")
        dummy_predictions_1 = [
            {'predicted_crop': 'Wheat', 'suitability_scores': {'Wheat': '90.50%', 'Rice': '8.00%', 'Maize': '1.50%'}}
        ]
        advice_1 = generate_planting_advice(dummy_predictions_1)
        for item in advice_1:
            print(f"Crop: {item['crop']} (Suitability: {item['suitability']})")
            print(f"Advice: {item['advice']}")

        # Example 2: Multiple crop predictions
        print("\n--- Test 2: Multiple Crop Predictions ---")
        dummy_predictions_2 = [
            {'predicted_crop': 'Rice', 'suitability_scores': {'Rice': '85.00%', 'Wheat': '10.00%', 'Cotton': '5.00%'}},
            {'predicted_crop': 'Maize', 'suitability_scores': {'Maize': '75.60%', 'Sugarcane': '20.40%', 'Rice': '4.00%'}}
        ]
        advice_2 = generate_planting_advice(dummy_predictions_2)
        for item in advice_2:
            print(f"Crop: {item['crop']} (Suitability: {item['suitability']})")
            print(f"Advice: {item['advice']}")

        # Example 3: Prediction with a less common crop (testing model's general knowledge)
        print("\n--- Test 3: Less Common Crop ---")
        dummy_predictions_3 = [
            {'predicted_crop': 'Sorghum', 'suitability_scores': {'Sorghum': '65.20%', 'Maize': '30.00%', 'Wheat': '4.80%'}}
        ]
        advice_3 = generate_planting_advice(dummy_predictions_3)
        for item in advice_3:
            print(f"Crop: {item['crop']} (Suitability: {item['suitability']})")
            print(f"Advice: {item['advice']}")

        # Example 4: Model not available (simulated by setting generator to None, though load_nlp_model covers this)
        print("\n--- Test 4: NLP Model Not Available (Simulated Fallback) ---")
        original_generator = text_generator_pipeline # Save original
        text_generator_pipeline = None # Simulate failure

        advice_4 = generate_planting_advice(dummy_predictions_1) # Reuse dummy_predictions_1
        for item in advice_4:
            print(f"Crop: {item['crop']} (Suitability: {item['suitability']})")
            print(f"Advice: {item['advice']}")

        text_generator_pipeline = original_generator # Restore for any subsequent tests if needed

    print("\n--- Crop NLP Generator Test Complete ---")
