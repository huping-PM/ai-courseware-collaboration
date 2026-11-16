'use strict';
// The stable entry opens in its approved initial layout; existing conversations remain in history.
if(!scene){const previousSetCurrent=setCurrent,previousRender=render;const initial=blank();store.s.push(initial);current=initial;resultOpen=false;selected=null;render();
function enterCollaboration(){persist();window.internalStateTransition=true;location.href='内容协作状态原型.html?project='+project+'&session='+encodeURIComponent(current.id)}
setCurrent=function(s){if(s.artifacts.length){current=s;enterCollaboration()}else previousSetCurrent(s)};
render=function(){if(current.artifacts.length){enterCollaboration();return}previousRender()};
}
