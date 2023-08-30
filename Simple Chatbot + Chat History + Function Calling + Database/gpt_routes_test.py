from cmd import PROMPT
import openai
from flask import Blueprint, request, jsonify, session as flask_session, json
from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os


gpt_bp = Blueprint('gpt_bp', __name__)

#database config
engine = create_engine('sqlite:///test_db.db')
Session = sessionmaker(bind=engine)

#read a text file
text_file = os.path.join(os.path.dirname(__file__), 'test_db.txt')
with open(text_file, "r") as file:
    database_structure_txt = file.read()
    
functions = [
    {
        "name": "query_SQL_Lite_db",
        "description": "Queries a SQL Lite database to answer user's questions",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "An SQL Lite query"} 
            },
            "required": ["prompt"]
        }
    }
]

    
def execute_sql_query_function(prompt):

    # Create a new Session for this request
    session = Session()
    response_message = ""

    sql_query=prompt
    
    try:
        # Execute the SQL query
        result = session.execute(text(sql_query))

        if "INSERT" in sql_query.upper():
            session.commit()
            response_message = "Successfully inserted into database."

        elif "SELECT" in sql_query.upper():
            rows = result.fetchall()
            column_names = result.keys()
            formatted_rows = [tuple(round(value, 2) if isinstance(value, (float, int)) else value for value in row) for row in rows]
            response_message = json.dumps(formatted_rows)

    except Exception as e:
        print(f"An error occurred: {e}")
        session.rollback()
        response_message = f"An error occurred: {e}"

    finally:
        session.close()

    return response_message


@gpt_bp.route('/generate_gpt_response', methods=['POST'])
def generate_gpt_response():

    user_input = request.form.get('user_input')
    chat_history = flask_session.get('chat_history', [])
    print("Initial Chat History:", chat_history)  # Debug print
    chat_history.append({"role": "user", "content": user_input})
    chat_history = chat_history[-5:]

    system_message = (
    f"You are a virtual assistant for me, Serghei, and I built a database to interact with. Here is the structure of the database to help you formulate any SQL Lite queries needed when calling functions: {database_structure_txt}"
    "Call functions to retrieve data from the databse as needed"
    "In addition, you don't need to tell the user what query you used, just show them the data"
    )

    messages=[

            {"role": "system", "content": system_message},


    ]

    messages.extend(chat_history)  # Add chat history to the messages array
    print("Chat history after appending user input:", chat_history)  # Debug print


    # Create the chat completion
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo-0613',
        messages=messages,
        temperature=.1,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        n=1,
        functions=functions,
        function_call="auto",
        stop=None
    )
    
    response_message = response['choices'][0]['message']



    if response_message.get("function_call"):
        available_functions = {
            "query_SQL_Lite_db" : execute_sql_query_function, # First "FUNCTION_NAME" is the name of the function described, and second is the method/function that you will call in your code
        }
        function_name = response_message["function_call"]["name"] # Get the function name from GPT's response
        function_to_call = available_functions[function_name] # match the function name to the actual method/function in code
        function_args = json.loads(response_message["function_call"]["arguments"]) # Get the arguments defined in function
        function_response = function_to_call(
            prompt=function_args.get("prompt") # Extract the prompt from the arguments to pass to method/function
        )

        # Check if the function_response is null and handle it accordingly
        if function_response == [[None]]:
            function_response_content = "The response from executing the function in null, relay to user."
        else:
            function_response_content = function_response

        response_dict = {"role": "function", "name": function_name, "content": function_response_content} # Create a dictionary out of the function name/response of function to append to chat history
        chat_history.append(response_dict) # append the above dictionary to chat history
        chat_history = chat_history[-5:] # Keep only the last 5 messages
        flask_session['chat_history'] = chat_history 

        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages,
        )

        content = second_response['choices'][0]['message']['content'] # extract content portion of the message
        content_dict = {"role": "assistant", "content": content} # Create a dictionary with the desired structure to append to chat chistory

        chat_history.append(content_dict)
        chat_history = chat_history[-5:]  # Keep only the last 5 messages
        flask_session['chat_history'] = chat_history
        return jsonify({'answer': content})

    else:
        assistant_message = {"role": "assistant", "content": response_message['content']}
        if assistant_message['content'] is not None:
            chat_history.append(assistant_message)
        chat_history = chat_history[-5:]  # Keep only the last 5 messages
        flask_session['chat_history'] = chat_history

        return jsonify({'answer': assistant_message['content']})




