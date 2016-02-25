/*
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
*/
var app = angular
	.module('StarterApp', [
    'ngMaterial', 
    'ngRoute'
  ])
	.config(
    function($mdThemingProvider, $routeProvider, $locationProvider) {
  	  // Some theming for Angular Material
      $mdThemingProvider.theme('default')
  	    .primaryPalette('teal', {'hue-3':'50'})
  	    .accentPalette('indigo');

      $locationProvider.html5Mode({enabled: true,requireBase: false}).hashPrefix('!');
      
      // ng-view routing
      $routeProvider
        .when('/', {
          templateUrl: './app/templates/welcome.html',
          controller  : 'WelcomeCtrl'
        })
        .when('/rated', {
          templateUrl: './app/templates/rated.html',
          controller  : 'RatedCtrl'
        })
        .otherwise({
          redirectTo: '/'
        });
  	});

app.controller('AppCtrl', ['$scope', '$mdSidenav', function($scope, $mdSidenav){
  $scope.toggleSidenav = function(menuId) {
    $mdSidenav(menuId).toggle();
  };

  $scope.filterHC = function(item){
    return (item.type == 'cottage' || item.type == 'house');
  }
 
}]);

app.controller('WelcomeCtrl', ['$scope', '$http', function($scope, $http){
  $http({
    method: 'POST',
    url: '/api/get_recommendations'
  }).then(function successCallback(response) {
    $scope.recommendations = response.data.recommendations;
  }, function errorCallback(response) {
    console.log('error', response)
  });
}]);  

app.controller('RatedCtrl', ['$scope', '$http', function($scope, $http){
  $http({
    method: 'POST',
    url: '/api/get_rated'
  }).then(function successCallback(response) {
    console.log(response)
    $scope.rated = response.data.rated;
  }, function errorCallback(response) {
    console.log('error', response)
  });
}]); 