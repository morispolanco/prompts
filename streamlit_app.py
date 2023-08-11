import streamlit as st
import itertools
from prettytable import PrettyTable

# ... previous definitions and set up ...

def generate_candidate_prompts(description, test_cases, number_of_prompts):
  # ... previous code ...
  prompts = []

  for i in outputs.choices:
    prompts.append(i.message.content)
  return prompts

def generate_optimal_prompt(description, test_cases, number_of_prompts=10, use_wandb=False): 
  # ... previous code ...

  if use_wandb:
    wandb.config.update({"description": description, 
                        "test_cases": test_cases})

  prompts = generate_candidate_prompts(description, test_cases, number_of_prompts)
  prompt_ratings = test_candidate_prompts(test_cases, description, prompts)

  # Print the final ELO ratings
  table = PrettyTable()
  table.field_names = ["Prompt", "Rating"]
  for prompt, rating in sorted(prompt_ratings.items(), key=lambda item: item[1], reverse=True):
      table.add_row([prompt, rating])
      if use_wandb:
         wandb_table.add_data(prompt, rating)

  if use_wandb: # log the results to a Weights & Biases table and finish the run
    wandb.log({"prompt_ratings": wandb_table})
    wandb.finish()
  st.table(table)

def test_candidate_prompts(test_cases, description, prompts):
  # Initialize each prompt with an ELO rating of 1200
  prompt_ratings = {prompt: 1200 for prompt in prompts}
  
  # Calculate total rounds for progress bar
  total_rounds = len(test_cases) * len(prompts) * (len(prompts) - 1) // 2

  progress = st.progress(0)
  
  rounds = 0
  # For each pair of prompts
  for prompt1, prompt2 in itertools.combinations(prompts, 2):
    # For each test case
    for test_case in test_cases:
      rounds += 1
      progress.progress(rounds/total_rounds)
      
      # Generate outputs for each prompt
      generation1 = get_generation(prompt1, test_case)
      generation2 = get_generation(prompt2, test_case)
      
      # Rank the outputs
      score1 = get_score(description, test_case, generation1, generation2, RANKING_MODEL, RANKING_MODEL_TEMPERATURE)
      score2 = get_score(description, test_case, generation2, generation1, RANKING_MODEL, RANKING_MODEL_TEMPERATURE)

      # Convert scores to numeric values
      score1 = 1 if score1 == 'A' else 0 if score1 == 'B' else 0.5
      score2 = 1 if score2 == 'B' else 0 if score2 == 'A' else 0.5

      # Average the scores
      score = (score1 + score2) / 2

      # Update ELO ratings
      r1, r2 = prompt_ratings[prompt1], prompt_ratings[prompt2]
      r1, r2 = update_elo(r1, r2, score)
      prompt_ratings[prompt1], prompt_ratings[prompt2] = r1, r2

      # Print the winner of this round
      if score > 0.5:
        st.write(f"Winner: {prompt1}")
      elif score < 0.5:
        st.write(f"Winner: {prompt2}")
      else:
        st.write("Draw")
  
  return prompt_ratings
