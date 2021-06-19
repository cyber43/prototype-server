# -*- coding: utf-8 -*-
from flask_restx import Resource, Namespace
from flask import request
from flask_login import login_required, current_user
from flask.helpers import make_response
from flask.templating import render_template
from .service import GitlabImpl
from logger.log import log
from .dto.gitlabDTO import CreateGroupRequestDto, CreateGroupResponseDto, CreateAppRequestDto
from apis.gitlab.models import ServiceProject, UserProjectMappingEntity
from db.db import db
from .models import ServiceApp, UserAppMappingEntity
from apis.jenkins.models import JenkinsJob
from config.jenkins_config import get_jenkins_host

ns = Namespace('gitlab', version="1.0", description='gitlab controller')

@ns.route("/healthcheck")
class Index(Resource):
    @ns.doc(response={200: "success"})
    def get(self):
        return "This is a gitlab api healthcheck"

@ns.route("/project/create")
class Create(Resource):
    '''
        Gitlab Project 생성
    '''
    @ns.doc(response={200: "success"})
    def get(self):
        return make_response(render_template())
    
    @ns.doc(response={200: "success"})
    def post(self):
        response = ''
        return make_response(render_template())

@ns.route("/user/signup")
class Create(Resource):
    '''
        Gitlab 계정 생성
    '''
    @ns.doc(response={200: "success"})
    def get(self):
        return make_response(render_template())
    
    @ns.doc(response={200: "success"})
    def post(self):
        response = ''
        return make_response(render_template())

@ns.route("/users")
class Create(Resource):
    '''
        Gitlab 계정목록
    '''
    @ns.doc(response={200: "success"})
    def get(self):
        gitlabAPI = GitlabImpl()
        response = gitlabAPI.getUsers()

        response_data = []
        for data in response['data']:
            _dict = {
                'id': data['id'],
                'email': data['email'],
                'stats': data['state']
            }
            response_data.append(_dict)

        log.debug('----------------------')
        log.debug(response_data)
        log.debug('----------------------')
        return make_response(render_template('gitlab/users.html', response_code=response['status'], users=response_data))


@ns.route('/createproject')
class CreateProject(Resource):
    '''
        serivce 프로젝트(gitlab group) 생성
    '''

    @ns.doc(response={200: 'success'})
    @login_required
    def get(self):
        return make_response(render_template('gitlab/createproject.html'))

    @ns.doc(response={200: 'success'})
    @login_required
    def post(self):
        projectname = request.form.get('projectname')
        gitlabAPI = GitlabImpl()
        
        html_page = ''
        data = None
        
        try:
            post_data = CreateGroupRequestDto(name=projectname, path=projectname).__dict__
            response = gitlabAPI.createGroup(post_data, current_user.email)

            createGroupResponseDto = CreateGroupResponseDto(group_id=response['data'].get('id'),
            group_url=response['data'].get('web_url'))
            html_page = 'gitlab/createprojectsuccess.html'
            data = createGroupResponseDto.__dict__
        except Exception as e:
            log.error("[Error 313] 프로젝트 생성 요청 오류: {}".format(e))
            html_page = 'gitlab/createprojectfailed.html'
            data = "project create is failed. errocode 313"

        return make_response(render_template(html_page, data=data))

@ns.route('/createapp')
class CreateAPP(Resource):
    '''
        애플리케이션(fork gitlab project) 생성
    '''

    @ns.doc(response={200: 'success'})
    @login_required
    def get(self):
        # get project list
        # query reference: https://weicomes.tistory.com/262
        project_infos = []
        
        for u, v in db.session.query(ServiceProject, UserProjectMappingEntity).\
            filter(UserProjectMappingEntity.user_id == current_user.id).\
            filter(UserProjectMappingEntity.project_id == ServiceProject.id):
            project_info = {
                'project_id': u.id, # service_project table primary_key
                'project_name': u.project_name # gitlab group_name
            }
            project_infos.append(project_info)

        return make_response(render_template('gitlab/createapp.html', project_infos=project_infos))

    @ns.doc(response={200: 'success'})
    @login_required
    def post(self):

        html_page = 'gitlab/createappfailed.html'

        try:
            app_type = request.form.get('apptype')
            app_name = request.form.get('appname')
            project_id = request.form.get('projectid') # service_project table primary_key

            gitlabAPI = GitlabImpl()
            response = gitlabAPI.createApp(CreateAppRequestDto(app_type, app_name, project_id).__dict__)

            if response['status']:
                html_page = 'gitlab/createappsuccess.html'

        except Exception as e:
            log.error("[Error 314] 앱 생성 실패: {}".format(e))

        return make_response(render_template(html_page))

@ns.route('/app_dashboard')
class GetApp(Resource):
    '''
        애플리케이션 목록
    '''

    @ns.doc(response={200: 'success'})
    @login_required
    def get(self):
        # get project list
        # query reference: https://weicomes.tistory.com/262
        application_infos = []
        
        joinquery_result = db.session.query(UserAppMappingEntity, ServiceApp).\
            filter(UserAppMappingEntity.user_id == current_user.id).\
            filter(UserAppMappingEntity.app_id == ServiceApp.id).\
            all()

        for mapping, app in joinquery_result:
            application_info = {
                'projectname': '',
                'appname': '',
                'gitlab_url': '',
                'jenkins_url': '',
                'jenkins_jobpath': '',
                'deploy_url': ''
            }
            # get group name
            app_name = app.project_name
            group = ServiceProject.query.filter_by(id=app.group_id).first()
            group_name = group.project_name

            # get jenkins url
            jenkinsjob = JenkinsJob.query.filter_by(id=app.id).first()
            jenkinsjob_name = jenkinsjob.job_name
            jenkins_url = '{}job/{}/job/{}'.format(get_jenkins_host(), group_name, jenkinsjob_name)

            application_info['jenkins_url'] = jenkins_url
            application_info['jenkins_jobpath'] = '{}and{}and{}'.format(group_name, jenkinsjob_name, jenkinsjob.id)
            application_info['projectname'] = group_name
            application_info['appname'] = app_name
            application_info['gitlab_url'] = app.weburl
            application_info['deploy_url'] = f'{group_name}/{app_name}'
            application_infos.append(application_info)

        return make_response(render_template('gitlab/application_dashboard.html', application_infos=application_infos))
