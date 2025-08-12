////////////////////////////////////////////////////////////
// PLUGINS
////////////////////////////////////////////////////////////
function checkContentHeight(target){
	var stageHeight=$( window ).height();
	var newHeight = (stageHeight/2)-(target.height()/2);
	return newHeight;
}

function checkContentWidth(target){
	var stageWidth=$( window ).width();
	var newWidth = (stageWidth/2)-(target.width()/2);
	return newWidth;
}

function shuffle(array) {
	var currentIndex = array.length
	, temporaryValue
	, randomIndex
	;
	
	// While there remain elements to shuffle...
	while (0 !== currentIndex) {
		// Pick a remaining element...
		randomIndex = Math.floor(Math.random() * currentIndex);
		currentIndex -= 1;
		
		// And swap it with the current element.
		temporaryValue = array[currentIndex];
		array[currentIndex] = array[randomIndex];
		array[randomIndex] = temporaryValue;
	}
	
	return array;
}

function randomBoolean(){
    return Math.random() < 0.5;
}

function getDistance(sx, sy, ex, ey) {
	var dis = Math.sqrt(Math.pow(sx - ex, 2) + Math.pow(sy - ey, 2));
	return dis;
}

function sortOnObject(array, object, rev) {
	if(rev){
		array.sort(function(a, b){
			var a1= a[object], b1= b[object];
			if(a1== b1) return 0;
			return a1< b1? 1: -1;
		});
	}else{
		array.sort(function(a, b){
			var a1= a[object], b1= b[object];
			if(a1== b1) return 0;
			return a1> b1? 1: -1;
		});
	}
	return array;
}

function randomIntFromInterval(min,max){
    return Math.floor(Math.random()*(max-min+1)+min);
}

function addCommas(nStr) {
    nStr += '';
    x = nStr.split('.');
    x1 = x[0];
    x2 = x.length > 1 ? '.' + x[1] : '';
    var rgx = /(\d+)(\d{3})/;
    while (rgx.test(x1)) {
        x1 = x1.replace(rgx, '$1' + ',' + '$2');
    }
    return x1 + x2;
}

function swapArray(input, index_A, index_B) {
    var temp = input[index_A];
 
    input[index_A] = input[index_B];
    input[index_B] = temp;
}

function getCenterPosition(startX, startY, endX, endY) {
	var pos = {x:0, y:0}
    pos.x=(startX+endX)/2;
    pos.y=(startY+endY)/2;
	return pos;
}

function getCenterPositionByPercent(startX, startY, endX, endY, totalPercent, percent) {
	percent = percent > totalPercent ? totalPercent : percent;
	var pos = {x:0, y:0}
    pos.x=(startX+endX)/2;
    pos.y=(startY+endY)/2;
	return pos;
}

function getAnglePosition(x1, y1, radius, angle){
	var pos = {x:0, y:0};
    pos.x = x1 + radius * Math.cos(angle * Math.PI/180);
    pos.y = y1 + radius * Math.sin(angle * Math.PI/180);
	return pos;
}

function isEven(n) {
	n = Number(n);
	return n === 0 || !!(n && !(n%2));
  }