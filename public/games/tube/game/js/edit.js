////////////////////////////////////////////////////////////
// EDIT PUZZLE
////////////////////////////////////////////////////////////
var edit = {show:true, option:'', isLandscape:true, pointNum:0};
var editShapeData = {width:4, curveWidth:2, stroke:2, line:'#fff', editLine:'#e94b35', editFill:"#ccff00", edit:'#00ff00', curve:'#f3c501', dot:'#e87f05', start:'#c23825', end:'#e64595', alpha:.5};
var editDot, editShape, editShapeAll;
var tubeLoader, tubeFileFest;
var puzzleLoader, puzzleFileFest;

/*!
 * 
 * EDIT READY
 * 
 */
$(function() {
	$.editor.enable = true;
});

function loadEditPage(){
	optionsContainer.removeChild(buttonExit);
	
	$.get('editTools.html', function(data){
		$('body').prepend(data);
		$('#editWrapper').show();
		toggleEditOption();
		buildEditButtons();
		buildEditCanvas();

		levelDisplayContainer.visible = false;
		statusContainer.visible = false;
		timerContainer.visible = false;
		buttonSettings.visible = false;
	});		
}

function buildEditCanvas(){
	editAllContainer = new createjs.Container();

	editDot = new createjs.Shape();
	editDot.alpha = .5;
	editDot.graphics.beginFill(editShapeData.edit).drawCircle(0, 0, editShapeData.width+5);
	editDot.visible = false;
	editShape = new createjs.Shape();
	editShapeAll = new createjs.Shape();
	
	stage.addEventListener("dblclick", function(evt) {
		if(edit.option == 'tubeshape'){
			actionDrawingPoint('new');
		}
	});
}

/*!
 * 
 * BUILD EDIT BUTTONS - This is the function that runs to build edit buttons
 * 
 */
function buildEditButtons(){
	$('#toggleShowOption').click(function(){
		toggleShowOption();
	});
	
	$("#viewport").change(function() {
		if($(this).val() != ''){
			if($(this).val() == 'true'){
				viewport.isLandscape = edit.isLandscape = true;	
			}else{
				viewport.isLandscape = edit.isLandscape = false;
			}
			
			changeViewport(viewport.isLandscape);
			resizeGameFunc();
		}
	});
	
	//puzzles list
	gameData.levelNum = 0;
	buildLevelDropdown();
	
	$('#togglePanel').click(function(){
		togglePanel();
	});
	
	$("#levelsList").change(function() {
		if($(this).val() != ''){
			gameData.levelNum = $(this).val();
			loadLevelData();
		}
	});
	
	$('#prevLevel').click(function(){
		toggleLevel(false);
	});
	
	$('#nextLevel').click(function(){
		toggleLevel(true);
	});
	
	$('#addLevel').click(function(){
		actionLevel('new');
	});
	
	$('#removeLevel').click(function(){
		actionLevel('remove');
	});
	
	$('#moveLevelUp').click(function(){
		actionLevel('moveup');
	});
	
	$('#moveLevelDown').click(function(){
		actionLevel('movedown');
	});
	
	$('#editLevel').click(function(){
		toggleEditOption('level', true);
	});

	$('#editTubes').click(function(){
		toggleEditOption('tubes', true);
	});

	$('#updateLevel').click(function(){
		updateLevelData();
	});

	$('#doneLevel').click(function(){
		toggleEditOption();
	});
	
	//generate
	$('#generateArray').click(function(){
		generateArray();
	});

	toggleLevel(false);
	toggleLevel(true);

	//tube
	buildTubeDD();
	
	$("#tubelist").change(function() {
		if($(this).val() != ''){
			gameData.tubeNum = $(this).val();
			loadTubeAssets();
		}
	});
	
	$('#addTube').click(function(){
		actionTube("new");
	});
	
	$('#removeTube').click(function(){
		actionTube("remove");
	});
	
	$('#prevTube').click(function(){
		toggleEditTube(false);
	});
	
	$('#nextTube').click(function(){
		toggleEditTube(true);
	});

	//edit
	$('#updateImage').click(function(){
		loadTubeAssets();
	});
	
	$('#doneTube').click(function(){
		toggleEditOption('tubes', true);
	});

	$('#removePoint').click(function(){
		actionDrawingPoint('remove');
	});
	
	//option
	$('#editTube').click(function(){
		toggleEditOption('tubeshape');
	});
	
	$('#generateTubeArray').click(function(){
		generateTubeArray();
	});

	$('#cancelTube').click(function(){
		toggleEditOption();
		loadEditPuzzle();
	});
}

 /*!
 * 
 * TOGGLE DISPLAY OPTION - This is the function that runs to toggle display option
 * 
 */
 
function toggleShowOption(){
	if(edit.show){
		edit.show = false;
		$('#editOption').hide();
		$('#toggleShowOption').val('Show Edit Option');
	}else{
		edit.show = true;
		$('#editOption').show();
		$('#toggleShowOption').val('Hide Edit Option');
	}
}

/*!
 * 
 * TOGGLE EDIT OPTION - This is the function that runs to toggle edit option
 * 
 */
function toggleEditOption(con){
	edit.option = con;
	edit.option = edit.option == undefined ? "default" : edit.option;
	
	$('#selectLevelWrapper').hide();
	$('#editLevelWrapper').hide();
	$('#levelEditWrapper').hide();
	$('#editTubesWrapper').hide();
	$('#tubeWrapper').hide();
	$('#hiddenEditWrapper').hide();

	if(con == 'level'){
		$('#selectLevelWrapper').show();
		$('#levelEditWrapper').show();
	}else if(con == 'tubes'){
		$('#editTubesWrapper').show();
		loadTubeAssets();
	}else if(con == 'tubeshape'){
		$('#tubeWrapper').show();
		buildDrawingData();
	}else{
		$('#selectLevelWrapper').show();
		$('#editLevelWrapper').show();
	}
}


/*!
 * 
 * BUILD PUZZLE DROPDOWN - This is the function that runs to build puzzle dropdown
 * 
 */
function buildLevelDropdown(){
	$('#levelsList').empty();
	for(var n=0;n<levelSettings.length;n++){
		$('#levelsList').append($("<option/>", {
			value: n,
			text: 'Level '+(n+1)
		}));
	}
	$('#levelsList').val(gameData.levelNum);
	
	loadLevelData();
}

/*!
 * 
 * TOGGLE PUZZLE - This is the function that runs to toggle puzzle
 * 
 */
function toggleLevel(con){
	if(con){
		gameData.levelNum++;
		gameData.levelNum = gameData.levelNum > levelSettings.length - 1 ? 0 : gameData.levelNum;
	}else{
		gameData.levelNum--;
		gameData.levelNum = gameData.levelNum < 0 ? levelSettings.length - 1 : gameData.levelNum;
	}
	
	$('#levelsList').prop("selectedIndex", gameData.levelNum);
	loadLevelData();
}

/*!
 * 
 * LOAD EDITOR PUZZLE - This is the function that runs to load editor data
 * 
 */
function loadLevelData(){
	$('#levelTimer').val(levelSettings[gameData.levelNum].timer);
	$('#levelScore').val(levelSettings[gameData.levelNum].score);
	$('#levelTubes').val(levelSettings[gameData.levelNum].tubes);
	$('#levelEmptyTubes').val(levelSettings[gameData.levelNum].empty);
	$('#levelLevels').val(levelSettings[gameData.levelNum].levels);
	$('#levelHidden').val(String(levelSettings[gameData.levelNum].hidden));
	$('#levelColumn').val(levelSettings[gameData.levelNum].column);
	$('#levelMarginX').val(levelSettings[gameData.levelNum].marginX);
	$('#levelMarginY').val(levelSettings[gameData.levelNum].marginY);
	$('#levelPortraitColumn').val(levelSettings[gameData.levelNum].portrait.column);
	$('#levelPortraitMarginX').val(levelSettings[gameData.levelNum].portrait.marginX);
	$('#levelPortraitMarginY').val(levelSettings[gameData.levelNum].portrait.marginY);

	loadEditPuzzle();
}

/*!
 * 
 * EDITOR ACTION - This is the function that runs to for editor action
 * 
 */
function actionLevel(action){
	switch(action){
		case 'new':
			levelSettings.push({
				timer:60000,
				score:500,
				tubes:3,
				empty:1,
				levels:4,
				hidden:false,
				column:3,
				marginX:40,
				marginY:50,
				portrait:{
					column:3,
					marginX:40,
					marginY:50,
				}
			});
			gameData.levelNum = levelSettings.length - 1;
			buildLevelDropdown();
		break;
		
		case 'remove':
			if(levelSettings.length > 1){
				levelSettings.splice(gameData.levelNum, 1);
				gameData.levelNum = 0;
				buildLevelDropdown();
			}
		break;
		
		case 'moveup':
			if(gameData.levelNum-1 >= 0){
				swapArray(levelSettings, gameData.levelNum-1, gameData.levelNum);
				gameData.levelNum--;
				buildLevelDropdown();
			}
		break;
		
		case 'movedown':
			if(gameData.levelNum+1 < levelSettings.length){
				swapArray(levelSettings, gameData.levelNum+1, gameData.levelNum);
				gameData.levelNum++;
				buildLevelDropdown();
			}
		break;
	}
}

/*!
 * 
 * UPDATE PUZZLE - This is the function that runs to update puzzle
 * 
 */
function updateLevelData(){
	levelSettings[gameData.levelNum].timer = Number($('#levelTimer').val());
	levelSettings[gameData.levelNum].score = Number($('#levelScore').val());
	levelSettings[gameData.levelNum].tubes = Number($('#levelTubes').val());
	levelSettings[gameData.levelNum].empty = Number($('#levelEmptyTubes').val());
	levelSettings[gameData.levelNum].levels = Number($('#levelLevels').val());
	levelSettings[gameData.levelNum].hidden = $('#levelHidden').val() == 'true' ? true : false;
	levelSettings[gameData.levelNum].column = Number($('#levelColumn').val());
	levelSettings[gameData.levelNum].marginX = Number($('#levelMarginX').val());
	levelSettings[gameData.levelNum].marginY = Number($('#levelMarginY').val());
	levelSettings[gameData.levelNum].portrait.column = Number($('#levelPortraitColumn').val());
	levelSettings[gameData.levelNum].portrait.marginX = Number($('#levelPortraitMarginX').val());
	levelSettings[gameData.levelNum].portrait.marginY = Number($('#levelPortraitMarginY').val());

	loadEditPuzzle();
}

/*!
 * 
 * LOAD EDIT PUZZLE - This is the function that runs to load edit puzzle
 * 
 */
function loadEditPuzzle(){
	gameData.paused = false;
	gameData.action = false;
	gameData.offsetY = 0;
	gameData.resize = false;

	setupStage();
}

/*!
 * 
 * GENERATE ARRAY - This is the function that runs to generate array
 * 
 */
function generateArray(){
	var outputArray = '';
	var space = '					';
	var space2 = '						';
	var space3 = '							';
	var space4 = '								';
	
	outputArray += "[\n";
	for(var e=0;e<levelSettings.length;e++){
		outputArray += space+"{\n";
		outputArray += space2+'timer:'+levelSettings[e].timer+',\n';
		outputArray += space2+'score:'+levelSettings[e].score+',\n';
		outputArray += space2+'tubes:'+levelSettings[e].tubes+',\n';
		outputArray += space2+'empty:'+levelSettings[e].empty+',\n';
		outputArray += space2+'levels:'+levelSettings[e].levels+',\n';
		outputArray += space2+'hidden:'+levelSettings[e].hidden+',\n';
		outputArray += space2+'column:'+levelSettings[e].column+',\n';
		outputArray += space2+'marginX:'+levelSettings[e].marginX+',\n';
		outputArray += space2+'marginY:'+levelSettings[e].marginY+',\n';
		outputArray += space2+'portrait:{\n';
		outputArray += space3+'column:'+levelSettings[e].portrait.column+',\n';
		outputArray += space3+'marginX:'+levelSettings[e].portrait.marginX+',\n';
		outputArray += space3+'marginY:'+levelSettings[e].portrait.marginY+',\n';
		outputArray += space2+'}\n';
		outputArray += space+"},\n";
	}
						
	outputArray += '];';
	outputArray = outputArray.replace(/undefined/g,0);
	$('#outputArray').val(outputArray);	
}


/*!
 * 
 * BUILD TUBE DROPDOWN - This is the function that runs to build tube dropdown
 * 
 */
function buildTubeDD(){
	$('#tubelist').empty();
	
	for(var n=0;n<tubes_arr.length;n++){
		$('#tubelist').append($("<option/>", {
			value: n,
			text: 'Tube '+(n+1)
		}));
	}
}

/*!
 * 
 * TOGGLE TUBE - This is the function that runs to toggle tube
 * 
 */
function toggleEditTube(con){
	if(con){
		gameData.tubeNum++;
		gameData.tubeNum = gameData.tubeNum > tubes_arr.length - 1 ? 0 : gameData.tubeNum;
	}else{
		gameData.tubeNum--;
		gameData.tubeNum = gameData.tubeNum < 0 ? tubes_arr.length - 1 : gameData.tubeNum;
	}
	
	$('#tubelist').prop("selectedIndex", gameData.tubeNum);
	loadTubeAssets();
}

/*!
 * 
 * EDITOR ACTION - This is the function that runs to for editor action
 * 
 */
function actionTube(action){
	switch(action){
		case 'new':			
			tubes_arr.push({
				imageBack:"assets/tube_back_01.png",
				imageFront:"assets/tube_front_01.png",
				regX:44,
				regY:310,
				fillW:50,
				fillH:260,
				tubeW:60,
				tubeH:300,
				perspective:true,
				shape:[
					{x:-25, y:-277},
					{x:-25, y:-141},
					{x:-25, y:-22},
					{x:-19, y:1},
					{x:1, y:0},
					{x:18, y:0},
					{x:25, y:-22},
					{x:25, y:-132},
					{x:25, y:-276},
					{x:1, y:-271},
					{x:-25, y:-277},
					],
			});
							
			gameData.tubeNum = tubes_arr.length - 1;
			buildTubeDD();
			$('#tubelist').prop("selectedIndex", gameData.tubeNum);
			loadTubeAssets();	
		break;
		
		case 'remove':
			if(tubes_arr.length > 1){
				tubes_arr.splice(gameData.tubeNum, 1);
				gameData.tubeNum = 0;
				buildTubeDD();
				loadEditTube();	
			}
		break;
	}
}

/*!
 * 
 * LOAD EDIT TUBE - This is the function that runs to load tube value
 * 
 */
function loadEditTube(){
	$("#imageBack").val(tubes_arr[gameData.tubeNum].imageBack);
	$("#imageFront").val(tubes_arr[gameData.tubeNum].imageFront);
	$("#centerX").val(tubes_arr[gameData.tubeNum].regX);
	$("#centerY").val(tubes_arr[gameData.tubeNum].regY);
	$("#fillW").val(tubes_arr[gameData.tubeNum].fillW);
	$("#fillH").val(tubes_arr[gameData.tubeNum].fillH);
	$("#tubeW").val(tubes_arr[gameData.tubeNum].tubeW);
	$("#tubeH").val(tubes_arr[gameData.tubeNum].tubeH);

	var perValue = tubes_arr[gameData.tubeNum].perspective == true ? 1 : 0;
	$("#perspective").val(perValue);

	prepareStage();
	createTube(0,0);
	pushColours(0,0,tubes_arr[gameData.tubeNum].fillH);
	fillLiquid(0);
	updateTubeData(gameData.tubes[0]);
	buildDrawingData();

	gameData.offsetY = tubes_arr[gameData.tubeNum].fillH/2;
	resizeGameUI();
}

/*!
 * 
 * UPDATE QUESTION - This is the function that runs to update question value
 * 
 */
function updateTubeData(){
	tubes_arr[gameData.tubeNum].imageBack = $("#imageBack").val()
	tubes_arr[gameData.tubeNum].imageFront = $("#imageFront").val()
	tubes_arr[gameData.tubeNum].regX = Number($("#centerX").val());
	tubes_arr[gameData.tubeNum].regY = Number($("#centerY").val());
	tubes_arr[gameData.tubeNum].fillW = Number($("#fillW").val());
	tubes_arr[gameData.tubeNum].fillH = Number($("#fillH").val());
	tubes_arr[gameData.tubeNum].tubeW = Number($("#tubeW").val());
	tubes_arr[gameData.tubeNum].tubeH = Number($("#tubeH").val());
	tubes_arr[gameData.tubeNum].perspective = $('#perspective :selected').val() == "0" ? false : true;
}

/*!
 * 
 * BUILD DRAWING DATA - This is the function that runs to build drawing data
 * 
 */
function buildDrawingData(){
	editContainer.removeAllChildren();
	editContainer.addChild(editDot, editAllContainer, editShape);
	
	editShape.graphics.clear();
	editDot.visible = false;

	if(edit.option == 'tubeshape'){
		//gameData.tubes[0].data.colors.length = 0;
		//fillLiquid(0);
		if(tubes_arr[gameData.tubeNum].shape.length > 0){
			drawDots();
			drawEditLines();
		}
	}
}

/*!
 * 
 * EDITOR ACTION - This is the function that runs to for editor action
 * 
 */
function actionDrawingPoint(action){
	switch(action){
		case 'new':
			var local = editContainer.globalToLocal(stage.mouseX, stage.mouseY);
			var currentX = Math.round(local.x);
			var currentY = Math.round(local.y);

			if(tubes_arr[gameData.tubeNum].shape.length == 0){
				tubes_arr[gameData.tubeNum].shape.push({x:currentX, y:currentY}, {x:currentX+30, y:currentY+30},{x:currentX+40, y:currentY+40});
				edit.pointNum = 0;
			}else{
				var pointNum = edit.pointNum;
				if(isEven(edit.pointNum)){
					pointNum++;
				}
				tubes_arr[gameData.tubeNum].shape.splice(pointNum, 0, {x:currentX-30, y:currentY-30},{x:currentX, y:currentY});
				edit.pointNum = pointNum;
			}
			
			buildDrawingData();
		break;
		
		case 'remove':
			var pointNum = edit.pointNum;
			if(pointNum == 0 && tubes_arr[gameData.tubeNum].shape.length > 2){
				pointNum++;			
			}else{
				if(isEven(edit.pointNum)){
					pointNum--;
				}
			}

			tubes_arr[gameData.tubeNum].shape.splice(pointNum, 2);
			edit.pointNum = tubes_arr[gameData.tubeNum].shape.length-1;
			edit.pointNum = edit.pointNum < 0 ? 0 : edit.pointNum;
			editDot.visible = false;

			buildDrawingData();
		break;
	}
}

/*!
 * 
 * REDRAW POINT - This is the function that runs to redraw point
 * 
 */
function drawEditLines(){
	editShape.graphics.clear();
	editShape.alpha = editShapeData.alpha;
	
	if(tubes_arr[gameData.tubeNum].shape.length > 0){
		editShape.graphics.setStrokeStyle(editShapeData.stroke).beginStroke(editShapeData.editLine).beginFill(editShapeData.editFill).moveTo(tubes_arr[gameData.tubeNum].shape[0].x, tubes_arr[gameData.tubeNum].shape[0].y);
		for(var n=0;n<tubes_arr[gameData.tubeNum].shape.length;n++){
			if(tubes_arr[gameData.tubeNum].shape.length - n > 2 && isEven(n)){
				editShape.graphics.curveTo(tubes_arr[gameData.tubeNum].shape[n+1].x, tubes_arr[gameData.tubeNum].shape[n+1].y, tubes_arr[gameData.tubeNum].shape[n+2].x, tubes_arr[gameData.tubeNum].shape[n+2].y);
			}
		}
	}
}

/*!
 * 
 * DRAW ALL POINTS - This is the function that runs to draw all points
 * 
 */
function drawDots(){
	for(var n=0;n<tubes_arr[gameData.tubeNum].shape.length;n++){
		drawDot(n, tubes_arr[gameData.tubeNum].shape[n].x, tubes_arr[gameData.tubeNum].shape[n].y);
	}
}

/*!
 * 
 * DRAW SINGLE POINT - This is the function that runs to draw single point
 * 
 */
function drawDot(n,x,y){
	var circle = new createjs.Shape();
	var dotWidth = isEven(n) == true ? editShapeData.width : editShapeData.curveWidth;
	var colourCheckDot = isEven(n) == true ? editShapeData.dot : editShapeData.curve;
	colourCheckDot = n == 0 ? editShapeData.start : colourCheckDot;
	colourCheckDot = n == tubes_arr[gameData.tubeNum].shape.length-1 ? editShapeData.end : colourCheckDot;

	circle.graphics.setStrokeStyle(2).beginStroke('#fff');
	circle.graphics.beginFill(colourCheckDot).drawCircle(0, 0, dotWidth);
	circle.x = x;
	circle.y = y;
	circle.alpha = editShapeData.alpha;
	editContainer.addChild(circle);
	
	circle.cursor = "pointer";
	circle.name = n;
	circle.addEventListener("mousedown", function(evt) {
		toggleDragEvent(evt, 'drag')
	});
	circle.addEventListener("pressmove", function(evt) {
		toggleDragEvent(evt, 'move')
	});
	circle.addEventListener("pressup", function(evt) {
		toggleDragEvent(evt, 'drop')
	});
}

/*!
 * 
 * POINT EVENT - This is the function that runs to for point event handler
 * 
 */
function toggleDragEvent(obj, con){
	switch(con){
		case 'drag':
			obj.target.offset = {x:obj.target.x-(obj.stageX), y:obj.target.y-(obj.stageY)};
			obj.target.alpha = .5;
			
			edit.pointNum = obj.target.name;
			toggleEditDot(obj.target.x, obj.target.y, obj.target.name);
		break;
		
		case 'move':
			obj.target.alpha = .5;
			obj.target.x = (obj.stageX) + obj.target.offset.x;
			obj.target.y = (obj.stageY) + obj.target.offset.y;

			tubes_arr[gameData.tubeNum].shape[obj.target.name].x = Math.round(obj.target.x);
			tubes_arr[gameData.tubeNum].shape[obj.target.name].y = Math.round(obj.target.y);

			toggleEditDot(obj.target.x, obj.target.y, obj.target.name);
			drawEditLines();
		break;
		
		case 'drop':
			obj.target.alpha = 1;
		break;
	}
}

/*!
 * 
 * TOGGLE EDIT POINT - This is the function that runs to toggle edit point
 * 
 */
function toggleEditDot(x, y, name){
	editDot.x = x;
	editDot.y = y;
	editDot.visible = true;
}

/*!
 * 
 * GENERATE ARRAY - This is the function that runs to generate array
 * 
 */
function generateTubeArray(){
	var outputArray = '';
	var space = '					';
	var space2 = '						';
	var space3 = '							';
	
	outputArray += "[\n";
	for(var e=0;e<tubes_arr.length;e++){
		var shapeArray = '\n';
		for(var n = 0; n < tubes_arr[e].shape.length; n++){
			shapeArray += space3+'{'
			shapeArray += "x:" + tubes_arr[e].shape[n].x + ", y:" + Number(tubes_arr[e].shape[n].y);
			shapeArray += '},\n';
		}

		outputArray += space+"{\n";
		outputArray += space2+"imageBack:\""+tubes_arr[e].imageBack+"\",\n";
		outputArray += space2+"imageFront:\""+tubes_arr[e].imageFront+"\",\n";
		outputArray += space2+"regX:"+tubes_arr[e].regX+",\n";
		outputArray += space2+"regY:"+tubes_arr[e].regY+",\n";
		outputArray += space2+"fillW:"+tubes_arr[e].fillW+",\n";
		outputArray += space2+"fillH:"+tubes_arr[e].fillH+",\n";
		outputArray += space2+"tubeW:"+tubes_arr[e].tubeW+",\n";
		outputArray += space2+"tubeH:"+tubes_arr[e].tubeH+",\n";
		outputArray += space2+"perspective:"+tubes_arr[e].perspective+",\n";
		outputArray += space2+"shape:["+shapeArray+space3+"],\n";
		outputArray += space+"},\n\n";
	}
						
	outputArray += space+'];';
	outputArray = outputArray.replace(/undefined/g,0);
	$('#outputTubeArray').val(outputArray);	
}

/*!
 * 
 * LOAD TUBE ASSETS - This is the function that runs to load tube assets
 * 
 */ 
function loadTubeAssets(){	
	tubeFileFest = [];
	
	tubeFileFest.push({src:tubes_arr[gameData.tubeNum].imageBack, id:'tubeBack' + gameData.tubeNum});
	tubeFileFest.push({src:tubes_arr[gameData.tubeNum].imageFront, id:'tubeFront' + gameData.tubeNum});
	
	tubeLoader = new createjs.LoadQueue(false);
	tubeLoader.addEventListener("complete", handleTubeComplete);
	tubeLoader.loadManifest(tubeFileFest);
}

function handleTubeComplete() {
	loadEditTube();
};