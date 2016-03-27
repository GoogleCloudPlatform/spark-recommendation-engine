"""
Copyright Google Inc. 2016
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import cgi
import webapp2
import logging
import json

import MySQLdb

# Define your production Cloud SQL instance information.
_INSTANCE_NAME = '<YOUR-PROJECT_ID>:<YOUR-INSTANCE-NAME>'
_DB_NAME = '<YOUR-DB-NAME>'
_DB_USER = '<YOUR-DB-USER>'
_DB_PASS = '<YOUR-DB-PASS>'
_USER_ID = str(0)


# Returns a list of the accommodation that the user already rated
class GetRatedHandler(webapp2.RequestHandler):
  
  def post(self):
    # Connect to your DB
    db = MySQLdb.connect(unix_socket='/cloudsql/' + _INSTANCE_NAME, db=_DB_NAME, user=_DB_USER, passwd=_DB_PASS, charset='utf8')

    # Fetch the recommendations
    cursor = db.cursor()
    cursor.execute('SELECT  a.id, a.title, a.type, r.rating \
      FROM Rating r \
      INNER JOIN Accommodation a \
      ON r.accoId = a.id \
      WHERE userId = ' + _USER_ID)

    rated = []
    for r in cursor.fetchall():
      rated.append({
        'id': cgi.escape(r[0]),
        'title': cgi.escape(r[1]),
        'type': cgi.escape(r[2]),
        'rating': r[3]
      })

    json_response = json.dumps({
      'rated': rated
    })

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json_response)

  def get(self):
    self.get()


# Returns a list of the recommendations for the user previously recorded by the recommendation engine
class GetRecommendationHandler(webapp2.RequestHandler):
  
  def post(self):
    # Connect to your DB
    db = MySQLdb.connect(unix_socket='/cloudsql/' + _INSTANCE_NAME, db=_DB_NAME, user=_DB_USER, passwd=_DB_PASS, charset='utf8')

    # Fetch the recommendations
    cursor = db.cursor()
    cursor.execute('SELECT id, title, type, r.prediction \
      FROM Accommodation a \
      INNER JOIN Recommendation r \
      ON r.accoId = a.id \
      WHERE r.userId = ' + _USER_ID + ' \
      ORDER BY r.prediction desc')

    recommendations = []
    for acc in cursor.fetchall():
      recommendations.append({
        'id': cgi.escape(acc[0]),
        'title': cgi.escape(acc[1]),
        'type': cgi.escape(acc[2])
      })


    json_response = json.dumps({
      'recommendations': recommendations
    })

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json_response)

  def get(self):
    self.post()

api = webapp2.WSGIApplication([
    ('/api/get_recommendations', GetRecommendationHandler),
    ('/api/get_rated', GetRatedHandler)
  ],
  debug=True
)