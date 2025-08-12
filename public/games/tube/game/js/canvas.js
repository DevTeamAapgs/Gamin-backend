////////////////////////////////////////////////////////////
// CANVAS
////////////////////////////////////////////////////////////
var stage;
var canvasW=0;
var canvasH=0;

/*!
 * 
 * START GAME CANVAS - This is the function that runs to setup game canvas
 * 
 */
function initGameCanvas(w,h){
	const gameCanvas = document.getElementById("gameCanvas");
	gameCanvas.width = w;
	gameCanvas.height = h;
	
	canvasW=w;
	canvasH=h;
	stage = new createjs.Stage("gameCanvas",{ antialias: true });
	
	createjs.Touch.enable(stage);
	stage.enableMouseOver(20);
	stage.mouseMoveOutside = true;
	
	createjs.Ticker.framerate = 60;
	createjs.Ticker.addEventListener("tick", tick);
}

var safeZoneGuide = false;
var canvasContainer, mainContainer, gameContainer, resultContainer, exitContainer, optionsContainer, shareContainer, shareSaveContainer, socialContainer;
var guideline, bg, bgP, logo, logoP;
var itemExit, itemExitP, popTitleTxt, popDescTxt, buttonConfirm, buttonCancel;
var itemResult, itemResultP, buttonContinue, resultTitleTxt, resultDescTxt, buttonShare, buttonSave;
var resultTitleOutlineTxt,resultDescOutlineTxt,resultShareTxt,resultShareOutlineTxt,popTitleOutlineTxt,popDescOutlineTxt;
var buttonSettings, buttonFullscreen, buttonSoundOn, buttonSoundOff, buttonMusicOn, buttonMusicOff, buttonExit;
$.share = {};

var levelContainer,selectContainer,editContainer,editAllContainer,levelDisplayContainer,timerContainer,statusContainer,waterContainer;
var buttonStart,buttonLevels,selectLevelTitleTxt,buttonLevelArrowL,buttonLevelArrowR,buttonBack,selectTubeTitleTxt,buttonSelect,buttonArrowL,buttonArrowR,timerShapeBg,timerShape,levelTxt,statusTxt,resultlevelTxt;
$.tubes = {};
$.level = {};

/*!
 * 
 * BUILD GAME CANVAS ASSERTS - This is the function that runs to build game canvas asserts
 * 
 */
function buildGameCanvas(){
	canvasContainer = new createjs.Container();
	mainContainer = new createjs.Container();
	gameContainer = new createjs.Container();
	exitContainer = new createjs.Container();
	resultContainer = new createjs.Container();
	shareContainer = new createjs.Container();
	shareSaveContainer = new createjs.Container();
	socialContainer = new createjs.Container();

	levelContainer = new createjs.Container();
	selectContainer = new createjs.Container();
	editContainer = new createjs.Container();
	editAllContainer = new createjs.Container();
	levelDisplayContainer = new createjs.Container();
	timerContainer = new createjs.Container();
	statusContainer = new createjs.Container();
	waterContainer = new createjs.Container();	
	
	bg = new createjs.Bitmap(loader.getResult('background'));
	bgP = new createjs.Bitmap(loader.getResult('backgroundP'));

	logo = new createjs.Bitmap(loader.getResult('logo'));
	logoP = new createjs.Bitmap(loader.getResult('logoP'));
	
	buttonStart = new createjs.Bitmap(loader.getResult('buttonStart'));
	centerReg(buttonStart);

	buttonLevels = new createjs.Bitmap(loader.getResult('buttonLevels'));
	centerReg(buttonLevels);

	//levels
	//level
	var levelData = {sX:0, sY:0, x:0, y:0, space:5, size:80, count:0};
	var totalW = (selectData.column-1) * levelData.size;
	totalW += (selectData.column-1) * levelData.space;
	var totalH = (selectData.row-1) * levelData.size;
	totalH += (selectData.row-1) * levelData.space;

	levelData.sX = -(totalW/2);
	levelData.sY = -(totalH/2);
	levelData.y = levelData.sY;

	for(var r=0; r<selectData.row; r++){
		levelData.x = levelData.sX;
		for(var c=0; c<selectData.column; c++){
			$.level[r+'_'+c] = new createjs.Bitmap(loader.getResult('itemLevel'));
			centerReg($.level[r+'_'+c]);
			$.level[r+'_'+c].x = levelData.x;
			$.level[r+'_'+c].y = levelData.y;

			$.level[r+'_unlock_'+c] = new createjs.Bitmap(loader.getResult('itemLevelUnlocked'));
			centerReg($.level[r+'_unlock_'+c]);
			$.level[r+'_unlock_'+c].x = levelData.x;
			$.level[r+'_unlock_'+c].y = levelData.y;

			$.level[r+'_text_'+c] = new createjs.Text();
			$.level[r+'_text_'+c].font = "25px comicyregular";
			$.level[r+'_text_'+c].color = '#1E6D13';
			$.level[r+'_text_'+c].textAlign = "center";
			$.level[r+'_text_'+c].textBaseline='alphabetic';
			$.level[r+'_text_'+c].x = levelData.x;
			$.level[r+'_text_'+c].y = levelData.y + 12;

			$.level[r+'_unlock_'+c].text = $.level[r+'_text_'+c];

			levelContainer.addChild($.level[r+'_'+c], $.level[r+'_unlock_'+c], $.level[r+'_text_'+c]);
			
			levelData.x += levelData.size + levelData.space;
			levelData.count++;
		}
		levelData.y += levelData.size + levelData.space;
	}

	selectLevelTitleTxt = new createjs.Text();
	selectLevelTitleTxt.font = "45px comicyregular";
	selectLevelTitleTxt.color = '#fff';
	selectLevelTitleTxt.textAlign = "center";
	selectLevelTitleTxt.textBaseline='alphabetic';
	selectLevelTitleTxt.text = textStrings.selectLevel;

	buttonLevelArrowL = new createjs.Bitmap(loader.getResult('buttonArrowL'));
	centerReg(buttonLevelArrowL);
	buttonLevelArrowR = new createjs.Bitmap(loader.getResult('buttonArrowR'));
	centerReg(buttonLevelArrowR);
	buttonBack = new createjs.Bitmap(loader.getResult('buttonBack'));
	centerReg(buttonBack);

	levelContainer.addChild(selectLevelTitleTxt, buttonLevelArrowL, buttonLevelArrowR, buttonBack);

	//select
	selectTubeTitleTxt = new createjs.Text();
	selectTubeTitleTxt.font = "45px comicyregular";
	selectTubeTitleTxt.color = '#fff';
	selectTubeTitleTxt.textAlign = "center";
	selectTubeTitleTxt.textBaseline='alphabetic';
	selectTubeTitleTxt.text = textStrings.selectTube;

	buttonSelect = new createjs.Bitmap(loader.getResult('buttonSelect'));
	centerReg(buttonSelect);

	buttonArrowL = new createjs.Bitmap(loader.getResult('buttonArrowL'));
	centerReg(buttonArrowL);

	buttonArrowR = new createjs.Bitmap(loader.getResult('buttonArrowR'));
	centerReg(buttonArrowR);

	selectContainer.addChild(selectTubeTitleTxt, buttonSelect, buttonArrowL, buttonArrowR);
	
	//game
	timerShapeBg = new createjs.Shape();
	timerShape = new createjs.Shape();
	timerContainer.addChild(timerShapeBg, timerShape);

	levelTxt = new createjs.Text();
	levelTxt.font = "35px comicyregular";
	levelTxt.color = '#fff';
	levelTxt.textAlign = "center";
	levelTxt.textBaseline='alphabetic';
	levelTxt.text = '00:00';
	levelTxt.y = 20;

	levelDisplayContainer.addChild(levelTxt);

	statusTxt = new createjs.Text();
	statusTxt.font = "45px comicyregular";
	statusTxt.color = '#fff';
	statusTxt.textAlign = "center";
	statusTxt.textBaseline='alphabetic';

	statusContainer.addChild(statusTxt);

	//result
	itemResult = new createjs.Bitmap(loader.getResult('itemPop'));
	itemResultP = new createjs.Bitmap(loader.getResult('itemPopP'));
	
	buttonContinue = new createjs.Bitmap(loader.getResult('buttonContinue'));
	centerReg(buttonContinue);
	
	resultShareTxt = new createjs.Text();
	resultShareTxt.font = "20px comicyregular";
	resultShareTxt.color = '#37648E';
	resultShareTxt.textAlign = "center";
	resultShareTxt.textBaseline='alphabetic';
	resultShareTxt.text = textStrings.share;
	
	resultTitleTxt = new createjs.Text();
	resultTitleTxt.font = "45px comicyregular";
	resultTitleTxt.color = '#1A4970';
	resultTitleTxt.textAlign = "center";
	resultTitleTxt.textBaseline='alphabetic';
	resultTitleTxt.text = textStrings.resultTitle;
	
	resultlevelTxt = new createjs.Text();
	resultlevelTxt.font = "30px comicyregular";
	resultlevelTxt.color = '#37648E';
	resultlevelTxt.textAlign = "center";
	resultlevelTxt.textBaseline='alphabetic';
	resultlevelTxt.text = '';
	
	resultDescTxt = new createjs.Text();
	resultDescTxt.font = "60px comicyregular";
	resultDescTxt.color = '#37648E';
	resultDescTxt.textAlign = "center";
	resultDescTxt.textBaseline='alphabetic';
	resultDescTxt.text = '';
	
	socialContainer.visible = false;
	socialContainer.scale = .8;
	shareContainer.addChild(resultShareTxt, socialContainer);

	if(shareSettings.enable){
		buttonShare = new createjs.Bitmap(loader.getResult('buttonShare'));
		centerReg(buttonShare);
		
		var pos = {x:0, y:45, spaceX:65};
		pos.x = -(((shareSettings.options.length-1) * pos.spaceX)/2)
		for(let n=0; n<shareSettings.options.length; n++){
			var shareOption = shareSettings.options[n];
			var shareAsset = String(shareOption[0]).toUpperCase() + String(shareOption).slice(1);
			$.share['button'+n] = new createjs.Bitmap(loader.getResult('button'+shareAsset));
			$.share['button'+n].shareOption = shareOption;
			centerReg($.share['button'+n]);
			$.share['button'+n].x = pos.x;
			$.share['button'+n].y = pos.y;
			socialContainer.addChild($.share['button'+n]);
			pos.x += pos.spaceX;
		}
		buttonShare.y = (buttonShare.image.naturalHeight/2) + 10;
		shareContainer.addChild(buttonShare);
	}

	if ( typeof toggleScoreboardSave == 'function' ) { 
		buttonSave = new createjs.Bitmap(loader.getResult('buttonSave'));
		centerReg(buttonSave);
		buttonSave.y = (buttonSave.image.naturalHeight/2) + 10;
		shareSaveContainer.addChild(buttonSave);
	}
	
	//options
	buttonFullscreen = new createjs.Bitmap(loader.getResult('buttonFullscreen'));
	centerReg(buttonFullscreen);
	buttonSoundOn = new createjs.Bitmap(loader.getResult('buttonSoundOn'));
	centerReg(buttonSoundOn);
	buttonSoundOff = new createjs.Bitmap(loader.getResult('buttonSoundOff'));
	centerReg(buttonSoundOff);
	buttonSoundOn.visible = false;
	buttonMusicOn = new createjs.Bitmap(loader.getResult('buttonMusicOn'));
	centerReg(buttonMusicOn);
	buttonMusicOff = new createjs.Bitmap(loader.getResult('buttonMusicOff'));
	centerReg(buttonMusicOff);
	buttonMusicOn.visible = false;
	
	buttonExit = new createjs.Bitmap(loader.getResult('buttonExit'));
	centerReg(buttonExit);
	buttonSettings = new createjs.Bitmap(loader.getResult('buttonSettings'));
	centerReg(buttonSettings);
	
	createHitarea(buttonFullscreen);
	createHitarea(buttonSoundOn);
	createHitarea(buttonSoundOff);
	createHitarea(buttonMusicOn);
	createHitarea(buttonMusicOff);
	createHitarea(buttonExit);
	createHitarea(buttonSettings);
	optionsContainer = new createjs.Container();
	optionsContainer.addChild(buttonFullscreen, buttonSoundOn, buttonSoundOff, buttonMusicOn, buttonMusicOff, buttonExit);
	optionsContainer.visible = false;
	
	//exit
	itemExit = new createjs.Bitmap(loader.getResult('itemPop'));
	itemExitP = new createjs.Bitmap(loader.getResult('itemPopP'));
	
	buttonConfirm = new createjs.Bitmap(loader.getResult('buttonConfirm'));
	centerReg(buttonConfirm);
	
	buttonCancel = new createjs.Bitmap(loader.getResult('buttonCancel'));
	centerReg(buttonCancel);
	
	popTitleTxt = new createjs.Text();
	popTitleTxt.font = "45px comicyregular";
	popTitleTxt.color = "#1A4970";
	popTitleTxt.textAlign = "center";
	popTitleTxt.textBaseline='alphabetic';
	popTitleTxt.text = textStrings.exitTitle;
	
	popDescTxt = new createjs.Text();
	popDescTxt.font = "30px comicyregular";
	popDescTxt.lineHeight = 35;
	popDescTxt.color = "#37648E";
	popDescTxt.textAlign = "center";
	popDescTxt.textBaseline='alphabetic';
	popDescTxt.text = textStrings.exitMessage;
	
	exitContainer.addChild(itemExit, itemExitP, popTitleTxt, popDescTxt, buttonConfirm, buttonCancel);
	exitContainer.visible = false;
	
	guideline = new createjs.Shape();
	
	mainContainer.addChild(logo, logoP, buttonStart, buttonLevels);
	gameContainer.addChild(editContainer, levelDisplayContainer, timerContainer, statusContainer);
	resultContainer.addChild(itemResult, itemResultP, buttonContinue, resultTitleTxt, resultDescTxt, shareContainer, shareSaveContainer);
	
	canvasContainer.addChild(bg, bgP, mainContainer, levelContainer, waterContainer, selectContainer, gameContainer, resultContainer, exitContainer, optionsContainer, buttonSettings, guideline);
	stage.addChild(canvasContainer);
	
	changeViewport(viewport.isLandscape);
	resizeGameFunc();
}

function changeViewport(isLandscape){
	if(isLandscape){
		//landscape
		stageW=landscapeSize.w;
		stageH=landscapeSize.h;
		contentW = landscapeSize.cW;
		contentH = landscapeSize.cH;
	}else{
		//portrait
		stageW=portraitSize.w;
		stageH=portraitSize.h;
		contentW = portraitSize.cW;
		contentH = portraitSize.cH;
	}
	
	canvasW=stageW;
	canvasH=stageH;
	
	changeCanvasViewport();
}

function changeCanvasViewport(){
	if(canvasContainer!=undefined){
		stage.scaleX = stage.scaleY = dpr;
		
		if(safeZoneGuide){	
			guideline.graphics.clear().setStrokeStyle(2).beginStroke('red').drawRect((stageW-contentW)/2, (stageH-contentH)/2, contentW, contentH);
		}

		if(viewport.isLandscape){
			bg.visible = true;
			bgP.visible = false;

			logo.visible = true;
			logoP.visible = false;

			buttonStart.x = canvasW/2 - 100;
			buttonStart.y = canvasH/100 * 73;

			buttonLevels.x = canvasW/2 + 100;
			buttonLevels.y = canvasH/100 * 73;

			//select
			selectTubeTitleTxt.x = canvasW/2;
			selectTubeTitleTxt.y = canvasH/100 * 25;

			buttonSelect.x = canvasW/2;
			buttonSelect.y = canvasH/100 * 73;

			buttonArrowL.x = canvasW/2 - 130;
			buttonArrowL.y = canvasH/100 * 73;

			buttonArrowR.x = canvasW/2 + 130;
			buttonArrowR.y = canvasH/100 * 73;

			//game
			
			//result
			itemResult.visible = true;
			itemResultP.visible = false;

			buttonContinue.x = canvasW/2;
			buttonContinue.y = canvasH/100 * 67;
	
			shareContainer.x = shareSaveContainer.x = canvasW/2;
			shareContainer.y = shareSaveContainer.y = canvasH/100 * 52;
	
			resultTitleTxt.x = canvasW/2;
			resultTitleTxt.y = canvasH/100 * 37;
	
			resultDescTxt.x = canvasW/2;
			resultDescTxt.y = canvasH/100 * 46;

			//exit
			itemExit.visible = true;
			itemExitP.visible = false;

			buttonConfirm.x = (canvasW/2);
			buttonConfirm.y = (canvasH/100 * 58);
			
			buttonCancel.x = (canvasW/2);
			buttonCancel.y = (canvasH/100 * 68);

			popTitleTxt.x = canvasW/2;
			popTitleTxt.y = canvasH/100 * 37;
			
			popDescTxt.x = canvasW/2;
			popDescTxt.y = canvasH/100 * 42;

		}else{
			bg.visible = false;
			bgP.visible = true;

			logo.visible = false;
			logoP.visible = true;

			buttonStart.x = canvasW/2;
			buttonStart.y = canvasH/100 * 60;

			buttonLevels.x = canvasW/2;
			buttonLevels.y = canvasH/100 * 70;

			//select
			selectTubeTitleTxt.x = canvasW/2;
			selectTubeTitleTxt.y = canvasH/100 * 25;

			buttonSelect.x = canvasW/2;
			buttonSelect.y = canvasH/100 * 73;

			buttonArrowL.x = canvasW/2 - 130;
			buttonArrowL.y = canvasH/100 * 73;

			buttonArrowR.x = canvasW/2 + 130;
			buttonArrowR.y = canvasH/100 * 73;

			//game
			
			//result
			itemResult.visible = false;
			itemResultP.visible = true;

			buttonContinue.x = canvasW/2;
			buttonContinue.y = canvasH/100 * 63;
	
			shareContainer.x = shareSaveContainer.x = canvasW/2;
			shareContainer.y = shareSaveContainer.y = canvasH/100 * 51;
	
			resultTitleTxt.x = canvasW/2;
			resultTitleTxt.y = canvasH/100 * 40;
	
			resultDescTxt.x = canvasW/2;
			resultDescTxt.y = canvasH/100 * 47;
			
			//exit
			itemExit.visible = false;
			itemExitP.visible = true;

			buttonConfirm.x = (canvasW/2);
			buttonConfirm.y = (canvasH/100 * 56);
			
			buttonCancel.x = (canvasW/2);
			buttonCancel.y = (canvasH/100 * 64);

			popTitleTxt.x = canvasW/2;
			popTitleTxt.y = canvasH/100 * 40;
			
			popDescTxt.x = canvasW/2;
			popDescTxt.y = canvasH/100 * 44;
		}
	}
}



/*!
 * 
 * RESIZE GAME CANVAS - This is the function that runs to resize game canvas
 * 
 */
function resizeCanvas(){
 	if(canvasContainer!=undefined){
		
		buttonSettings.x = (canvasW - offset.x) - 50;
		buttonSettings.y = offset.y + 45;
		
		var distanceNum = 60;
		var nextCount = 0;
		buttonSoundOn.x = buttonSoundOff.x = buttonSettings.x;
		buttonSoundOn.y = buttonSoundOff.y = buttonSettings.y+distanceNum;
		buttonSoundOn.x = buttonSoundOff.x;
		buttonSoundOn.y = buttonSoundOff.y = buttonSettings.y+distanceNum;
		if (typeof buttonMusicOn != "undefined") {
			buttonMusicOn.x = buttonMusicOff.x = buttonSettings.x;
			buttonMusicOn.y = buttonMusicOff.y = buttonSettings.y+(distanceNum*2);
			buttonMusicOn.x = buttonMusicOff.x;
			buttonMusicOn.y = buttonMusicOff.y = buttonSettings.y+(distanceNum*2);
			nextCount = 2;
		}else{
			nextCount = 1;
		}
		buttonFullscreen.x = buttonSettings.x;
		buttonFullscreen.y = buttonSettings.y+(distanceNum*(nextCount+1));

		if(curPage == 'main' || curPage == 'result'){
			buttonExit.visible = false;			
			buttonFullscreen.x = buttonSettings.x;
			buttonFullscreen.y = buttonSettings.y+(distanceNum*(nextCount+1));
		}else{
			buttonExit.visible = true;			
			buttonExit.x = buttonSettings.x;
			buttonExit.y = buttonSettings.y+(distanceNum*(nextCount+2));
		}

		resizeGameUI();
	}
}

/*!
 * 
 * REMOVE GAME CANVAS - This is the function that runs to remove game canvas
 * 
 */
 function removeGameCanvas(){
	 stage.autoClear = true;
	 stage.removeAllChildren();
	 stage.update();
	 createjs.Ticker.removeEventListener("tick", tick);
	 createjs.Ticker.removeEventListener("tick", stage);
 }

/*!
 * 
 * CANVAS LOOP - This is the function that runs for canvas loop
 * 
 */ 
function tick(event) {
	updateGame();
	stage.update(event);
}

/*!
 * 
 * CANVAS MISC FUNCTIONS
 * 
 */
function centerReg(obj){
	obj.regX=obj.image.naturalWidth/2;
	obj.regY=obj.image.naturalHeight/2;
}

function createHitarea(obj){
	obj.hitArea = new createjs.Shape(new createjs.Graphics().beginFill("#000").drawRect(0, 0, obj.image.naturalWidth, obj.image.naturalHeight));	
}