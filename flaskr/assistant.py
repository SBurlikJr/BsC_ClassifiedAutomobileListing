import json

from openai import OpenAI
from flask import session, render_template, request, jsonify, Blueprint, redirect, url_for

from .models import CarModel, CarMaker, Listing, CarSetting
from . import db
from .config.assistant_config import OpenAIConfig

bp = Blueprint("assistant", __name__, url_prefix="/")

client = OpenAI(api_key=OpenAIConfig().get_key())

@bp.route("chat", methods=["POST", "GET"])
def chat():
    if request.method == "GET" and session:
        if "history" not in session:
            session["history"] = []

        return render_template("Home/assistant.html",
                               history=session["history"])
    if not session:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        if "history" not in session:
            session["history"] = []

        user_input = request.form["user_input"]

        bot_response = get_chatgpt_response(user_input)

        bot_response = json.loads(bot_response)

        print(bot_response)

        condition_less = ['<=', '<', '=<']
        condition_great = ['>=', '>', '=<']

        options = bot_response["options"]

        list_of_recommendations = []

        for recommendation in bot_response.get("recommendations"):
            list_of_recommendations.append(recommendation["model"])

        query = (db.session.query(Listing)
                 .join(CarSetting)
                 .join(CarModel)
                 .join(CarMaker)
                 .filter(CarModel.name.in_(list_of_recommendations)))

        if isinstance(options, dict):
            for field, sub_field in options.items():
                # for '<' and '>' checks
                if isinstance(sub_field, dict):
                    value = sub_field["value"]
                    condition = sub_field["condition"]
                    if field == 'year':
                        if condition in condition_less:
                            query = query.filter(CarSetting.year_of_issue <= value)
                        elif condition in condition_great:
                            query = query.filter(CarSetting.year_of_issue >= value)
                        elif condition == "=":
                            query = query.filter(CarSetting.year_of_issue == value)
                    if field == 'price':
                        if condition in condition_less:
                            query = query.filter(CarSetting.price <= value)
                        elif condition in condition_great:
                            query = query.filter(CarSetting.price >= value)
                        elif condition == "=":
                            query = query.filter(CarSetting.price == value)
                    if field == 'mileage':
                        if condition in condition_less:
                            query = query.filter(CarSetting.mileage <= value)
                        elif condition in condition_great:
                            query = query.filter(CarSetting.mileage >= value)
                        elif condition == "=":
                            query = query.filter(CarSetting.mileage == value)
                    if field == 'engine_capacity':
                        if condition in condition_less:
                            query = query.filter(CarSetting.engine_capacity <= value)
                        elif condition in condition_great:
                            query = query.filter(CarSetting.engine_capacity >= value)
                        elif condition in "=":
                            query = query.filter(CarSetting.engine_capacity == value)
                else:
                    if field == 'drivetrain':
                        query = query.filter(CarSetting.drivetrain == sub_field)
                    if field == 'transmission':
                        query = query.filter(CarSetting.transmission == sub_field)
                    if field == 'fuel_type':
                        query = query.filter(CarSetting.fuel_type == sub_field)

        query = query.all()

        list_of_recommendations = [recommendation['maker'] +
                                   " " + recommendation['model']
                                   for recommendation
                                   in bot_response.get('recommendations')]
        list_of_recommendations = ", ".join(list_of_recommendations)
        fail_response = (f"I'm sorry but I did not find anything like that in the listings that are currently present "
                         f"in our database. Try something different! "
                         f"However, the cars that I tried to recommend are: {list_of_recommendations}")

        print(query)

        query_result = ', '.join([f"<a href=\"/lists/{i.id}\" target=\"_blank\" rel=\"noopener noreferrer\">" + str(i.settings_l.year_of_issue) + ' ' +i.settings_l.models.makers.name + ' ' + i.settings_l.models.name + "</a>" for i in query])

        # Message history
        if query == []:
            session["history"].append({"user": user_input, "bot": fail_response})
        else:
            session["history"].append({"user": user_input, "bot": query_result})

        # JSON response
        if query == []:
            return jsonify({"user": user_input, "bot": fail_response})
        else:
            return jsonify({"user": user_input,
                            "bot": "Here's the listings we have that fits "
                                   "the best your description: " + query_result})


def get_chatgpt_response(user_input):
    """Function to get the response from ChatGPT API"""
    try:
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {"role": "system", "content": "You are a helpful assistant for suggesting cars based on user's requirements."},
                {"role": "user", "content": "Always reply briefly and recommend multiple options that meet requirements."},
                {"role": "user", "content": "Always reply with a json"},
                {"role": "user", "content": "Reply must contain maker and model."},
                {"role": "user", "content": "A parameter 'recommendations' must be used a key to a corresponding list of suggested cars."},
                {"role": "user", "content": "If user mentions anything about mileage, year, price or engine capacity, take it as a parameters and make sure to include the whether user wants lower/higher value depending on the request (example, 'not newer than 2012' is going to be 'year':  { 'value': 2012, 'condition': '<' }), make sure to use only '<' or '>'; if user specifies adjectives, like 'small', 'little', 'low', you must convert it to a number that is commonly considered like such adjective."},
                {"role": "user", "content": "If user mentions anything about drivetrain (RWD, FWD, etc.), transmission (automatic, manual) or fuel type (gasoline, diesel, hybrid, electric, etc.), take it as a parameter."},
                {"role": "user", "content": "If size is mentioned, ignore it as a parameter; do not put size into options."},
                {"role": "user", "content": "A parameter 'options' must be used as a key to a corresponding list of parameters."},
                {"role": "user", "content": user_input}
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, I encountered an error. Please try again."
