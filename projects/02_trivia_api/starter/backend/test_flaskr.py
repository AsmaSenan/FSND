import os
import unittest
import json
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy


from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}:{}@{}/{}".format('postgres', '3911986','localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
        
        # Initialize and assign a new question to insert it in the DB
        self.new_question = {
            'question': 'Who discovered penicillin?',
            'answer': 'Alexander Fleming',
            'difficulty': 3,
            'category': 2,
        }

    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
#---------------------------------------------------------------
# 3 - Successful Test to Retrieve Categories
#---------------------------------------------------------------
    def test_get_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_categories'])
        self.assertTrue(len(Category.query.all()))

#--------- Test Invalid Method => error code 405
    def test_405_invalid_method_post_categories(self):
        res = self.client().post('/categories')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Method not Allowed')


#---------------------------------------------------------------
# 2 - Successful Test to Retrieve Questions
#---------------------------------------------------------------
    def test_get_questions(self):
        res = self.client().get('/questions')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))

#--------- Test requesting beyond valid page => error code 404  
    def test_404_sent_requesting_beyond_valid_page(self):
        res = self.client().get('/questions?page=100')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')
        
#---------------------------------------------------------------
# 4 - Successful Test to DELETE Question
#---------------------------------------------------------------
    # def test_delete_question(self):
    #     res = self.client().delete('questions/27')
    #     data = json.loads(res.data)
    #     deleted_question = Question.query.filter(Question.id == 27).one_or_none()
    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(data['success'], True)
    #     self.assertEqual(data['deleted_id'], 27)
    #     self.assertTrue(data['total_questions'])
    #     self.assertTrue(len('questions'))
    #     self.assertEqual(deleted_question, None)

# #--------- Test if question does not exist => error code 422  
    def test_422_if_question_does_not_exist(self):
        res = self.client().delete('/questions/1000')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')


#---------------------------------------------------------------
# 5 - Successful Test to CREATE a new Question
#---------------------------------------------------------------
    # def test_create_question(self):
    #     res = self.client().post('/questions', json=self.new_question)
    #     data = json.loads(res.data)
        
    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(data['success'], True)

#--------- Test if question creation method not allowed => error code 405  
    def test_405_if_question_creation_not_allowed(self):
        res = self.client().post('/questions/45', json=self.new_question)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Method not Allowed')

#---------------------------------------------------------------
# 6 - Successful Test to Search for Question with returned results
#---------------------------------------------------------------
    def test_search_question_with_results(self):
        res = self.client().post('/questions', json={'searchTerm': 'title'})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertEqual(len(data['questions']), 2)

#--------- Successful Test to Search for Question without returned results 
    def test_search_question_without_results(self):
        res = self.client().post('/questions', json={'searchTerm': 5})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['total_questions'], 0)
        self.assertEqual(len(data['questions']), 0)

#---------------------------------------------------------------
# 6 - Successful Test to GET Questions Based on Category
#---------------------------------------------------------------
    def test_get_questions_by_category(self):
        res = self.client().get('/categories/1/questions')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertEqual(len(data['questions']), 2)
        self.assertEqual(data['current_category'], 'Science')

#--------- Test to get questions with wrong category => error code 404  
    def test_404_get_questions_with_wrong_category(self):
        res = self.client().get('/categories/50/questions')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')
        
#---------------------------------------------------------------
# 8 - Successful Test to Play the Quiz with parameters (category and previous questions)
#---------------------------------------------------------------
    def test_get_question_for_quiz_with_parameters(self):
        parameters = {"previous_questions":[1], "quiz_category": {"id": 4}}
        res = self.client().post("/quizzes", json=parameters)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertEqual(data['total_questions'], 4)

#--------- Test to get questions without parameters(category and previous questions) => error code 500  
    def test_500_get_question_for_quiz_without_questions(self):
        parameters = {}
        res = self.client().post("/quizzes", json=parameters)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 500)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Internal Server Error')


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()