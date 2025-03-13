from flask import Flask, render_template, jsonify, request, session
import json
import random
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_url_path="/static")
app.secret_key = os.urandom(24)  # Add secret key for session
client = OpenAI()


# Load both persona data files
def load_data():
    # Load retail banking personas
    with open("persona.json", "r") as file:
        retail_data = json.load(file)

    # Load wealth management personas
    with open("wealth.json", "r") as file:
        wealth_data = json.load(file)

    return retail_data, wealth_data


@app.route("/")
def home():
    retail_data, wealth_data = load_data()

    # Randomly select one retail client and one wealth client
    retail_client = random.choice(retail_data["retail_clients"])
    wealth_client = random.choice(wealth_data["clients"])

    # Create a combined data structure for the template
    client_data = {
        "retail": {
            "name": retail_client["name"],
            "age": retail_client["age"],
            "gender": retail_client["gender"],
            "job": retail_client["job"],
            "wealth": retail_client["wealth"],
            "nationality": retail_client["nationality"],
        },
        "private": {
            "name": f"{wealth_client['personal_information']['first_name']} {wealth_client['personal_information']['last_name']}",
            "age": calculate_age(
                wealth_client["personal_information"]["date_of_birth"]
            ),
            "gender": "Prefer not to say",
            "job": f"{wealth_client['personal_information']['position_title']} at {wealth_client['personal_information']['employer']}",
            "wealth": f"${wealth_client['financial_information']['total_net_worth']:,}",
            "nationality": wealth_client["personal_information"]["nationality"],
        },
    }

    # Store client data in session
    session["client_data"] = client_data

    return render_template("index.html", client_data=client_data)


def calculate_age(date_of_birth):
    from datetime import datetime

    birth_year = int(date_of_birth.split("-")[0])
    current_year = datetime.now().year
    return current_year - birth_year


def create_retail_system_prompt(client_data):
    return f"""You are a helpful and friendly retail banking assistant at JPMorgan Chase. You are currently speaking with {client_data['name']}, a {client_data['age']}-year-old {client_data['nationality']} who works as a {client_data['job']} with an annual income of {client_data['wealth']}.

Your role is to:
1. Provide clear, simple explanations of banking products and services
2. Focus on basic retail banking needs like savings, checking accounts, mortgages, and personal loans
3. Be approachable and use everyday language, avoiding complex financial terminology
4. Make suggestions based on the client's income level and job stability
5. Keep responses brief and to the point (2-3 sentences maximum)

Remember: You are speaking to a retail banking client. Keep advice practical and focused on personal banking needs.

Please respond in a friendly, concise manner."""


def create_private_system_prompt(client_data):
    return f"""You are an elite private banking relationship manager at JPMorgan Chase Private Bank. You are currently in discussion with {client_data['name']}, a distinguished {client_data['age']}-year-old {client_data['nationality']} who holds the position of {client_data['job']} with a significant net worth of {client_data['wealth']}.

Your mandate is to:
1. Deliver sophisticated, bespoke financial strategies
2. Focus on wealth preservation and global investment opportunities
3. Communicate with refined professionalism
4. Provide tailored recommendations for high-net-worth needs
5. Keep responses precise and impactful (2-3 sentences maximum)

Remember: You are advising a private banking client. Focus on sophisticated strategies while being concise.

Please provide precise, professional responses that reflect our exclusive private banking services."""


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message")

    # Use client data from session
    client_data = session.get("client_data")

    if not client_data:
        return jsonify({"error": "Session expired. Please refresh the page."})

    # Get responses for both personas
    retail_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": create_retail_system_prompt(client_data["retail"]),
            },
            {"role": "user", "content": message},
        ],
        temperature=0.7,
    )

    private_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": create_private_system_prompt(client_data["private"]),
            },
            {"role": "user", "content": message},
        ],
        temperature=0.7,
    )

    return jsonify(
        {
            "retail_response": retail_response.choices[0].message.content,
            "private_response": private_response.choices[0].message.content,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
