import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10  # defined how many questions per page as constants 

'''
to split question into pages. will take the request and the entire questions
'''
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
  
  # Set up CORS. Allow '*' for origins.
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
    return jsonify({ 
      "success": True, 
      'total_categories': len(categories),
      "categories": {category.id: category.type for category in categories},
      })

#---------------------------------------------------------------
# 2 - Retrieve Questions
#---------------------------------------------------------------
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
        search_results = Question.query.order_by(
          Question.id
        ).filter(
          Question.question.ilike(
            '%{}%'.format(searchTerm))
        ).all()
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
          'created_id': question.id,
          'total_questions': len(Question.query.all())
        })

    except:
      abort(400)

#---------------------------------------------------------------
# 6 - Questions Based on Category
#---------------------------------------------------------------
  @app.route('/categories/<int:category_id>/questions')
  def retrieve_questions_by_category(category_id):
    questions = Question.query.order_by(
      Question.id
    ).filter(
      Question.category == category_id
      ).all()
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
  @app.route("/quizzes", methods=['POST'])
  def get_question_for_quiz():
    if request.data:
      body = request.get_json()
      previous_questions = body.get('previous_questions', [])
      quiz_category = body.get('quiz_category', None)
      try:
        if quiz_category['id'] == 0:
          questions_query = Question.query.filter(
            Question.id.notin_(previous_questions)
          ).all()
        else:
          questions_query = Question.query.filter_by(
            category= quiz_category['id']
          ).filter(
            Question.id.notin_(previous_questions)
          ).all()
        length_of_available_question = len(questions_query)
        if length_of_available_question > 0:
          result = {
            "success": True,
            "questions": Question.format(
              questions_query[
                random.randrange(
                  0, length_of_available_question
                )
              ]
            ),
          }
        else:
          result = {
            "success": True,
            "questions": None
          }
        return jsonify(result)

      except Exception as e:
        print(e)
        abort(400)

    abort(422)
#---------------------------------------------------------------
# 9 - Error Handlers
#---------------------------------------------------------------
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

  @app.errorhandler(500)
  def not_found(error):
    return jsonify({
      "success": False, 
      "error": 500,
      "message": "Internal Server Error"
      }), 500
  
  
  return app

    