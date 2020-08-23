import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10
# to split question into pages. will take the request and the entire questions
def paginated_questions(request, questions):
  page = request.args.get('page', 1, type=int)
  start =  (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions_formated = [question.format() for question in questions]
  current_questions = questions_formated[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app, resources={r"/api/*": {"origins": "*"}})

  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

  
#---------------------------------------------------------------
# 3 - Retrieve Categories
#---------------------------------------------------------------

  @app.route('/categories')
  def retrieve_categories():
    categories = Category.query.order_by(Category.id).all()
    if len(categories) == 0:
      abort(404)
    # categories_formated = {category.format() for category in categories}
    return jsonify({ 
      "success": True, 
      'total_categories': len(categories),
      "categories": {category.id: category.type for category in categories},
      })

#---------------------------------------------------------------
# 2 - Retrieve Questions
#---------------------------------------------------------------
  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions')
  def retrieve_questions():
    questions = Question.query.order_by(Question.id).all()
    current_questions = paginated_questions(request, questions)

    if len(current_questions) == 0:
      abort(404)
    categories = Category.query.order_by(Category.id).all()
    
    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(Question.query.all()),
      "categories": {category.id: category.type for category in categories},
      "current_category": None
    })


#---------------------------------------------------------------
# 4 - DELETE Question
#---------------------------------------------------------------
  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:deleted_id>', methods=['DELETE'])
  def delete_question(deleted_id):
    try:
      deleted_question = Question.query.filter_by(id=deleted_id).one_or_none()

      if deleted_question is None:
        abort(404)

      deleted_question.delete()

      questions = Question.query.order_by(Question.id).all()
      current_questions = paginated_questions(request, questions)

      return jsonify({
        'success': True,
        'deleted_id': deleted_id,
        'questions': current_questions,
        'total_questions': len(Question.query.all()),
      })
    except:
      abort(422)
  
#---------------------------------------------------------------
# 5 - CREATE a new Question & 7 - Search for Question
#---------------------------------------------------------------

  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()

    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_difficulty = body.get('difficulty', None)
    category = body.get('category', None)
    searchTerm = body.get('searchTerm', None)

    try:
      if searchTerm:
        search_results = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(searchTerm))).all()
        current_questions = paginated_questions(request, search_results)

        return jsonify({
          'success': True,
          'questions': current_questions,
          'total_questions': len(current_questions),
          'current_category': None
        })
      else:
        question = Question(
          question=new_question,
          answer=new_answer,
          category=category,
          difficulty=new_difficulty
        )
        question.insert()

        return jsonify({
          'success': True,
          # 'created_id': question.id,
        })

    except:
      abort(422)

#---------------------------------------------------------------
# 6 - Questions Based on Category
#---------------------------------------------------------------
  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions')
  def retrieve_questions_by_category(category_id):
    questions = Question.query.order_by(Question.id).filter(Question.category == category_id).all()
    current_questions = paginated_questions(request, questions)

    if len(current_questions) == 0:
      abort(404)
    categories = Category.query.order_by(Category.id).all()
    chosen_category = Category.query.filter_by(id=category_id).one_or_none()
    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(Question.query.all()),
      "categories": {category.id: category.type for category in categories},
      "current_category": chosen_category.type
    })

#---------------------------------------------------------------
# 8 - Play the Quiz
#---------------------------------------------------------------
  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''

  @app.route("/quizzes", methods=['POST'])
  def get_question_for_quiz():
    if request.data:
      body = request.get_json()
      previous_questions = body.get('previous_questions', None)
      quiz_category = body.get('quiz_category', None)
      try:
        if quiz_category['id'] == 0:
          questions_query = Question.query.filter(Question.id.notin_(previous_questions)).all()
        else:
          questions_query = Question.query.filter_by(category= quiz_category['id']).filter(Question.id.notin_(previous_questions)).all()
        length_of_available_question = len(questions_query)
        if length_of_available_question > 0:
          result = {
            "success": True,
            "questions": Question.format(questions_query[random.randrange(0, length_of_available_question)]),
            "total_questions": length_of_available_question
          }
        else:
          result = {
            "success": True,
            "questions": None
          }
        
      except:  
        abort(422)
      finally:  
        return jsonify(result)
        
    abort(422)
#---------------------------------------------------------------
# 9 - Error Handlers
#---------------------------------------------------------------
  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False, 
      "error": 404,
      "message": "resource not found"
      }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False, 
      "error": 422,
      "message": "unprocessable"
      }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False, 
      "error": 400,
      "message": "bad request"
      }), 400

  @app.errorhandler(405)
  def not_found(error):
    return jsonify({
      "success": False, 
      "error": 405,
      "message": "Method not Allowed"
      }), 405
  
  
  return app

    