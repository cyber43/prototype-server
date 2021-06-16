# -*- coding: utf-8 -*-
from flask import request
from flask.helpers import make_response
from flask.templating import render_template
from flask_login.utils import login_required
from werkzeug.utils import redirect
from flask_restx import Resource, fields, Namespace
from flask_login import login_user, logout_user
from logger.log import log
from apis import api
from .models import User
from login.loginmanager import login_manager
from db.db import db
from .dto.UserCreateDto import UserCreateResponseDto, UserCreateDto
from .service import FlaskCreateUserService

ns = Namespace('auth', version="1.0", description='login and authentication')

# swagger 입출력
model = api.model('auth', {
    'id': fields.String(required=True, description='example1'),
    'name': fields.String(required=True, description='example2'),
})

@login_manager.user_loader
def load_user(user_id):
    '''
        회원 로그인시 실행되는 필터?
    '''
    user = User.query.get(int(user_id))
    log.debug('[*] user login: {}'.format(user.email))
    
    return user

@ns.route('/healthcheck')
class method_name(Resource):
    @ns.doc(response={200: "success"})
    def get(self):
        body = 'this is auth api'
        log.debug(body)
        return body

@ns.route('/signup')
class Signup(Resource):
    '''
        회원가입
    '''

    @ns.doc(response={200: "success"})
    def get(self):
        return make_response(render_template('auth/signup.html'))

    '''
        todo: form 유효값 검사
    '''
    @ns.doc(response={200: "success"})
    def post(self):

        userCreateDto = UserCreateDto(email=request.form.get('email'), password=request.form.get('password'), confirm_password=request.form.get('confirm_password'))
        flaskCreateUserService = FlaskCreateUserService(userCreateDto)
        response = flaskCreateUserService.CreateUser()
        
        if response['status']:
            # 회원가입 성공            
            response_data = UserCreateResponseDto(id=response['data']['id'], email=response['data']['email'])
            return make_response(render_template('auth/signup_success.html', data=response_data.__dict__))
        else:
            # 회원가입 실패
            return make_response(render_template('auth/signup_failed.html', errormsg=response['error_msg']))

@ns.route('/signin')
class Signin(Resource):
    '''
        로그인
    '''

    @ns.doc(response={200: "success"})
    def get(self):
        return make_response(render_template('auth/signin.html'))

    '''
        todo: form 유효값 검사
    '''
    @ns.doc(response={200: "success"})
    def post(self):
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user:
            return make_response(render_template('auth/login_failed.html', response="Please check your input"))

        if not user.check_password(password):
            return make_response(render_template('auth/login_failed.html', response="Please check your input"))
        
        login_user(user)

        return make_response(render_template('auth/login_success.html'))

@ns.route('/logout')
class Logout(Resource):
    @ns.doc(response={200: "success"})
    @login_required
    def get(self):
        logout_user()
        return make_response(redirect('/api/v1/index'))
