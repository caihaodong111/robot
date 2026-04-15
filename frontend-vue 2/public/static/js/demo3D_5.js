/************************************************************/
/*  JavaScript Functions									*/
/*  FILENAME: Script_04.css									*/
/************************************************************/

//GLOBAL VARIABLES
var yaw   = 0.0;	//Euler angles
var pitch = 0.0;
var roll  = 0.0;

//Primary rotation matrix - used to rotate aircraft in work coord system
//主旋转矩阵 - 用于在工作坐标系中旋转飞机
var r11 = 1, r12 = 0, r13 = 0;
var r21 = 0, r22 = 1, r23 = 0;
var r31 = 0, r32 = 0, r33 = 1;

//Viewpoint rotation matrix - used to rotate point of view of world system (never changes)
//Corresponds to yaw=45, pitch=22.5, roll=22.5
//【视角】视点旋转矩阵 - 用于旋转世界系统的视点（永不改变）

// //========= 对应yaw = 22.5，pitch = 45，roll = 22.5 ===============
// var s11 =  0.6532, s12 = -0.1036, s13 =  0.7499;
// var s21 =  0.2705, s22 =  0.9571, s23 = -0.1036;
// var s31 = -0.7072, s32 =  0.2705, s33 =  0.6532;

//对应 yaw=0，pitch=0，roll=0
// var s11 = 1, s12 = 0, s13 = 0;
// var s21 = 0, s22 = 1, s23 = 0;
// var s31 = 0, s32 = 0, s33 = 1;

//对应 yaw = 0，pitch = 0，roll= 180
var s11 = 1, s12 = 0, s13 = 0;
var s21 = 0, s22 = -1, s23 = -0.0001;
var s31 = 0, s32 = 0, s33 = -1;

//对应 yaw = 180，pitch = 0，roll=0
// var s11 = -1, s12 = -0.0001, s13 = 0;
// var s21 = 0, s22 = -1, s23 = 0;
// var s31 = 0, s32 = 0, s33 = -1;

//对应 yaw = 0，pitch = 45，roll= 0
// var s11 = 0.7071, s12 = 0, s13 = 0.7071;
// var s21 = 0, s22 = 1, s23 = 0;
// var s31 = -0.7072, s32 = 1, s33 = 0.7071;

//对应 yaw = 0，pitch = 0，roll= 90
// var s11 = 1, s12 = 0, s13 = 0;
// var s21 = 0, s22 = 0, s23 = -1;
// var s31 = 0, s32 = 1, s33 = 0;


//对应 yaw = -45，pitch = 0，roll= 90
// var s11 = 0.7071, s12 = 0, s13 = -0.7072;
// var s21 = -0.7072, s22 = 0, s23 = -0.7072;
// var s31 = 0, s32 = 1, s33 = 0;

//对应 yaw = 0，pitch = 0，roll= 45
// var s11 = 1, s12 = 0, s13 = 0;
// var s21 = 0, s22 = 0.7071, s23 = -0.7072;
// var s31 = 0, s32 = 0.7071, s33 = 0.7071;


//对应 yaw = -90，pitch = 0，roll= 180
// var s11 = 0, s12 = -1, s13 = -0.0001;
// var s21 = -1, s22 = -0.0001, s23 = -0.0001;
// var s31 = 0, s32 = 0, s33 = -1;


//对应yaw= 22.5，pitch = 180，roll= 15
// var s11 = -0.9239, s12 = -0.3697, s13 = 0.099;
// var s21 = -0.3827, s22 = 0.8923, s23 = -0.2392;
// var s31 = -0.0001, s32 = -0.2589, s33 = -0.966;

//对应yaw=45，pitch = 202.5，roll=22.5
// var s11 = -0.6533, s12 = -0.7569, s13 = 0.0205;
// var s21 = -0.6533, s22 = 0.5497, s23 = -0.5206;
// var s31 = 0.3826, s32 = -0.3536, s33 = -0.8536;

//========= 对应yaw = 45，pitch = 22.5，roll = 22.5 ===============
// var s11 =  0.6532, s12 = -0.5498, s13 =  0.5205;
// var s21 =  0.6532, s22 =  0.7568, s23 = -0.0206;
// var s31 = -0.3827, s32 =  0.3535, s33 =  0.8535;

//对应yaw = 45，pitch = 22.5，roll = 202.5
// var s11 =  0.6532, s12 =  0.5497, s13 = -0.5206;
// var s21 =  0.6532, s22 = -0.7569, s23 =  0.0205;
// var s31 = -0.3827, s32 = -0.3536, s33 = -0.8536;

//对应yaw = -45，pitch = 22.5，roll = 202.5
// var s11 = 0.6532, s12 = -0.7569, s13 = 0.0205;
// var s21 = -0.6533, s22 = -0.5498, s23 = 0.5205;
// var s31 = -0.3827, s32 = -0.3536, s33 = -0.8536;

var shapeArray1;	//Aircraft in normalized position 飞机处于正常位置
var shapeArray2;	//Aircraft in modified position 飞机在修改位置
var shaddowArray;	//Aircraft shadow in modified position projected on grid 修改位置的飞机阴影投射到网格上
var plotOrder;		//True means facets get plotted in natural order, false = reverse order True 表示刻面以自然顺序绘制，false = 反向顺序

var gridArray1;		//Grid in normalized position 归一化位置的网格
var gridArray2;		//Grid in modified position 修改位置的网格

var axisArray1;		//Six lines that define 3 axes(normalized - never changed) 定义 3 个轴的六行（标准化 - 从未改变）
var axisArray2;		//Six lines that define 3 axes(rotated with scene - same every time) 定义 3 个轴的六线（随场景旋转 - 每次都相同）

var robot1_srcArray1 = [];   // robot1 src point array
var robot1_srcArray2 = [];

var robot2_srcArray1;   // robot2 src point array
var robot2_srcArray2;

var robot1_srcObj;   // the object of the feedback from Django
var robot2_srcObj;

var p_Array_1;            // 自定义point坐标
var p_Array_2;

var signal_defineArrays;
var signal_rotateScene;

var context;	//Drawing context  绘图上下文
var width;		//Canvas width
var height;		//Canvas height
var zGridLevel = 87;	//Z value for all pixels in grid  网格中所有像素的 Z 值


/************************************************************/
/* myInit()													*/
/* This function is called once at beginning, when page		*/
/* is loaded.												*/
/************************************************************/
function myInit(){

	console.log("- now in myInit ...")

	signal_defineArrays = false;
	signal_rotateScene = false;

	robot1_srcArray1 = []
	robot2_srcArray1 = []

	var canvas = document.getElementById("userCanvas");
	// var canvas2 = document.getElementById("userCanvas");
	
	// getContext() 方法返回一个用于在画布上绘图的环境,Canvas.getContext(contextID)
	// 当前唯一的合法值是 "2d"，它指定了二维绘图，并且导致这个方法返回一个环境对象，该对象导出一个二维绘图 API
	context = canvas.getContext("2d");
	width = canvas.width;
	height = canvas.height;
	
	xc = width/9;   // XYZ center
	yc = height/2;

	// handleClick();
	/****************************************************/
	/* Read Euler angle values from input cells			*/
	/****************************************************/
	// yaw   = document.getElementById("yawData").value;
	// pitch = document.getElementById("pitchData").value;
	// roll  = document.getElementById("rollData").value;

	yaw   = 0.0;
	pitch = 0.0;
	roll  = 0.0;
	
	/****************************************************/
	/* Error Check: Replace any invalid entries with 0	*/ 
	/****************************************************/
	if( isNaN(yaw) )
	{
		yaw = 0.0;
		document.getElementById("yawData").value = yaw;
	}
	if( isNaN(pitch) )
	{
		pitch = 0.0;
		document.getElementById("pitchData").value = pitch;
	}
	if( isNaN(roll) )
	{
		roll = 0.0;
		document.getElementById("rollData").value = roll;
	}
	
	/****************************************************/
	/* Compute rotation matrix and write to screen		*/ 
	/* 计算旋转矩阵并写入屏幕 */
	/****************************************************/
	computeRotationMatrix();
	

	// defineAircraftShapeArray();	//Populates shapeArray1, shapeArray2, shaddowArray
	defineGridShapeArray();		//Populates gridArray1, gridArray2
	defineAxesArrowArrays();	//Populates axisArray1, axisArray2 填充axisArray1、axisArray2
	definePointsArrays();  // 自定义point的Array
	defineRobotArrays();   // 机器人src程序读取 robot1_srcArray1, robot2_srcArray1

	/****************************************************/
	/* Rotate entire scene using rotation matrix S		*/
	/* Rotate aircraft, shadow, grid, and axes arrows	*/
	/* 使用旋转矩阵 S 旋转整个场景   (S * gridArray1, S * axisArray1)  */
	/* 首次更新 gridArray2, axisArray2 */
	/* 首次更新 p_Array_2 */
	/****************************************************/
	rotateScene();
	
	/****************************************************/
	/* Draw the graphics in the canvas					*/ 
	/* 使用gridArray2的数据绘制grid网格                   */
	/* 使用axisArray2的数据绘制axis坐标轴                 */
	/* 使用pointArray2的数据绘制自定义point坐标           */
	/* 使用robot1_pointArray2的数据绘制自定义point坐标    */
	/* 使用robot2_pointArray2的数据绘制自定义point坐标    */
	/****************************************************/
	drawAllGraphics()

}


/************************************************************/
/* drawAllGraphics()										*/
/* Draws shadow, grid, axes, and aircraft.					*/
/************************************************************/
function drawAllGraphics(){
	// context.clearRect(x,y,width,height) 清空给定矩形内的指定像素
	context.clearRect ( 0 , 0 , width, height ); 	//清除画布进行绘图
	
	/****************************************************/
	/* Draw the grid from gridArray2[lines][6]			*/
	/* 从 gridArray2[lines][6] 绘制网格 */
	/****************************************************/
	//Array is organized as: gridArray[line][x1,y1,z1,x2,y2,z2] (start point, end point)
	context.lineWidth = 1.0;
	context.strokeStyle = 'rgba(0,0,255,0.5)';
	for( var i=0; i < gridArray2.length; i++ ){
		context.beginPath();
		context.moveTo( xc + gridArray2[i][0], yc + gridArray2[i][1] );
		context.lineTo( xc + gridArray2[i][3], yc + gridArray2[i][4] );
		context.stroke();
	}

	/****************************************************/
	/* Draw the Axis graphic							*/
	/* 绘制坐标轴图形 */
	/* 通过axisArray2的数据绘制Axis */
	/****************************************************/
	drawAxes();
	drawAxes();
	
	/****************************************************/
	/* Draw the user defined Point  					*/
	/* 绘制自定义点                                      */
	/****************************************************/
	drawPoint();

	/****************************************************/
	/* read robot program coordinate */
	/* 绘制机器人src程序的点 */
	/****************************************************/
	
	
	context.font = "bold 10px Arial";
	context.fillStyle = 'rgba(0,0,0,1.0)';
	context.fillText("X",xc+76,yc-10);  // mark axis X
	context.fillText("Y",xc+10,yc-76);  // mark axis Y
	// context.fillText("Z",96,225);
	
}

/************************************************************/
/* defineGridShapeArray()									*/
/* Creates and populates gridArray1 with the lines that 	*/
/* make up the grid.   										*/
/* Also creates and populates gridArray2 with the same data	*/
/* Called once from myInit() at beginning of program.		*/
/* 定义GridShapeArray() */
/* 创建并使用以下行填充 gridArray1 */
/* 组成网格。 */
/* 还使用相同的数据创建和填充 gridArray2 */
/* 在程序开始时从 myInit() 调用一次。 */
/************************************************************/
function defineGridShapeArray()
{
	//Array defines the lines that make up the (x,y) grid.
	//Array is organized as: gridArray[line][x1,y1,z1,x2,y2,z2] (start point, end point)
	//So length of each dimension is [total_num_lines][6]
	//Array 定义构成 (x,y) 网格的线。
	//数组组织为：gridArray[line][x1,y1,z1,x2,y2,z2]（起点，终点）
	//所以每个维度的长度是[total_num_lines][6]
	var numLines = 11;		//Number of grid lines in each dimension.  Must be be odd.  This is half the total lines (x & y)
	var pixPerLine = 10;	//Spacing between lines
	var startPix = -pixPerLine*(numLines-1)/2;
	
	gridArray1 = new Array(numLines*2);	//Total lines in X and Y X和Y方向线的总共数目
	for( var n=0; n<numLines; n++ )
	{
		gridArray1[2*n]   = new Array(6);	//Start and end points for x parallel lines x 平行线的起点和终点
		gridArray1[2*n+1] = new Array(6);	//Start and end points for y parallel lines y 平行线的起点和终点
		//Lines parallel to X axis 平行于 X 轴的线
		gridArray1[2*n][0]   = startPix + n*pixPerLine;	//X coord
		gridArray1[2*n][1]   = startPix;				//Y coord
		gridArray1[2*n][2]   = zGridLevel;				//Z coord
		gridArray1[2*n][3]   = startPix + n*pixPerLine;	//X coord
		gridArray1[2*n][4]   = -startPix;				//Y coord
		gridArray1[2*n][5]   = zGridLevel;				//Z coord
		//Lines parallel to Y axis 平行于 Y 轴的线
		gridArray1[2*n+1][0] = startPix;				//X coord
		gridArray1[2*n+1][1] = startPix + n*pixPerLine;	//Y coord
		gridArray1[2*n+1][2] = zGridLevel;				//Z coord
		gridArray1[2*n+1][3] = -startPix;				//X coord
		gridArray1[2*n+1][4] = startPix + n*pixPerLine;	//Y coord
		gridArray1[2*n+1][5] = zGridLevel;				//Z coord
	}
	
	//Create gridArray2 and copy data into it
	gridArray2 = new Array(numLines*2);
	for( var n=0; n<numLines*2; n++ ){
		gridArray2[n]   = new Array(6);
		for( var j=0; j<6; j++ ){
			gridArray2[n][j] = gridArray1[n][j];
		}
	}
}


/************************************************************/
/* defineAxisArrowArrays()									*/
/* Defines points used to draw the three cardinal axes, and	*/
/* the arrow tips at the ends of them.   					*/
/* Called once from myInit() at beginning of program.		*/
/* axisArray[6][4][3]										*/
/* axisArray[numLines][points_per_line][dimensions]			*/
/* 定义AxisArrowArrays() */
/* 定义用于绘制三个基本轴的点，并且 */
/* 它们末端的箭头提示。 */
/* 在程序开始时从 myInit() 调用一次。 */
/* 轴数组[6][4][3] */
/* axisArray[numLines][points_per_line][dimensions] */
/************************************************************/
function defineAxesArrowArrays()
{
	//alert("IN: defineAxesArrowArrays()");
	var b = 80;		//Distance from origin to end of axes 从原点到轴末端的距离
	var c = 6;		//Length of arrow tip along shaft 箭头沿轴的长度

	axisArray1 = 
		[[[-b, 0, 0], [   0,   0,   0], [  0,   0,   0], [ 0, 0, 0], [ 0, 0, 0]],	//Negative end of X axis
		 [[ b, 0, 0], [ b-c,-c/2,   0], [b-c, c/2,   0], [ b, 0, 0], [ 0, 0, 0]],	//Positive end of X axis (with arrow)
		 [[ 0,-b, 0], [   0,   0,   0], [  0,   0,   0], [ 0, 0, 0], [ 0, 0, 0]],	//Negative end of Y axis
		 [[ 0, b, 0], [ -c/2, b-c,  0], [  c/2, b-c, 0], [ 0, b, 0], [ 0, 0, 0]],	//Positive end of Y axis (with arrow)
		 
		 [[ 0, 0, -b],[   0,   0,   0], [  0,   0,   0], [ 0, 0, 0], [ 0, 0, 0]],	//Negative end of Z array
		 [[ 0, 0, zGridLevel], [ 0,  -c/2,  zGridLevel-c], [ 0,  c/2,  zGridLevel-c], [0,  0,  zGridLevel], [ 0,  0,  0]]];  //Positive end of Z array

	axisArray2	= new Array(axisArray1.length);

	for( var i=0; i < axisArray1.length; i++ )	//Number of lines
	{		
		axisArray2[i] = new Array(axisArray1[i].length);
		for( var j=0; j < axisArray1[i].length; j++)	//Number of points in line
		{	
			axisArray2[i][j] = new Array(3);				//Number of dimensions (x,y,z)
		}
	}
	//alert("OUT: defineAxesArrowArrays()");
}


/************************************************************/
/* definePointsArrays()									*/
/************************************************************/
function definePointsArrays(points_list)
{
	p_Array_1 = [[3000,0,666],[0,3000,666],[0,-3000,666]]  // P1,P2 ...
	// console.log(p_Array_1.length)  // 2

	p_Array_2 = new Array(p_Array_1.length);
	for( var j=0; j < p_Array_1.length; j++)	//Number of points
	{	
		p_Array_2[j] = new Array(3);		    //Number of dimensions (x,y,z)
	}
}


/************************************************************/
/* defineRobotArrays()									*/
/************************************************************/
function defineRobotArrays(points_list)
{
	/* 1. 读取用户输入robot1和robot2的名称 */
	/* 2. 发送ajax请求读取对应机器人的src文件，得到src程序运动点的坐标列表 */
	var radios_coll_shops = document.getElementsByName("coll_shops");
	var shop_name = ""
	for(i = 0;i < radios_coll_shops.length; i++){
		radio = radios_coll_shops[i];
		if(radio.checked){
			shop_name = radio.value;
			// console.log(shop_name);
			break;
		}
	};
	var robot1 = document.getElementById("coll_robot1").value;
	var robot2 = document.getElementById("coll_robot2").value;

	console.log("!!!!!!!!!!! " + shop_name +"-"+ robot1 +'-'+ robot2);

	read_robot_coordinates(shop_name,robot1,robot2);  // send the request to Django to get the data	

	// console.log(p_Array_2)
	// robot1_pointArray1 = []

	// axisArray2	= new Array(robot1_pointArray1.length);

	// for( var i=0; i < robot1_pointArray1.length; i++ )	//Number of lines
	// {		
	// 	robot1_pointArray2[i] = new Array(robot1_pointArray1[i].length);
	// 	for( var j=0; j < robot1_pointArray1[i].length; j++)	//Number of points in line
	// 	{	
	// 		robot1_pointArray2[i][j] = new Array(3);				//Number of dimensions (x,y,z)
	// 	}
	// }
}



/************************************************************************/
/* drawAxes()															*/
/* Draws the X,Y,Z axes, and labels them.								*/
/* 通过axisArray2的数据绘制Axis
/************************************************************************/
function drawAxes()
{
	//axisArray[numLines][points_per_line][dimensions] = [6][4][3]
	// var xc = width/2;
	// var yc = height/2;
	
	context.lineWidth = 2.0;
	context.strokeStyle = 'rgba(255,0,0,0.5)';
	context.fillStyle   = 'rgba(255,0,0,0.5)';
	
	console.log("---------- drawAxes -------------")
	// console.log(axisArray2)
	
	// axisArray[6][4][3]  X-, X+, Y-, Y+ , Z-, Z+
	for( var i=0; i < axisArray2.length; i++)		//Loop over lines
	// for( var i=0; i < 6; i++)		//Loop over lines
	{		
		context.beginPath();
		// context.moveTo( xc + axisArray2[i][0][1], yc + axisArray2[i][0][2] );  //Project to Y and Z dimensions (投影到 y 和 Z 维度)
		context.moveTo( xc + axisArray2[i][0][0], yc + axisArray2[i][0][1] );	  //Project to X and Y dimensions (投影到 X 和 Y 维度)
		for( var j = 1; j < axisArray2[0].length; j++ )	//Loop over points in line
		{
			context.lineTo( xc + axisArray2[i][j][0], yc + axisArray2[i][j][1] );
			// console.log(xc + axisArray2[i][j][0] + " " + yc + axisArray2[i][j][1]);
		}
		context.stroke();
		context.fill();
	}
}


/*************************************/
/* 在坐标系中绘制一个自定义的点		 */
/* 通过 p_Array_2 的数据绘制Points    */
/*************************************/
function drawPoint(){
	scaling_down = 15;  // +++++++++++++++++++++++ 长度缩小比例 +++++++++++++++++++++++++
	// radius = 3  // radius of the point
	radius = 2.67  // radius of the point
	context.lineWidth = 1.0;
	context.strokeStyle = 'rgba(255,0,0,0.5)';  // stroke color for the point
	context.fillStyle   = 'rgba(255,0,0,0.5)';  // fill color for the point
	
	// P = [210, -200, 100]

	// console.log("---------- drawPoint -------------")
	// context.beginPath();
	// // context.arc(x,y,r,sAngle,eAngle,counterclockwise);  False = 顺时针，true = 逆时针
	// context.arc(xc+P[0], yc+P[1],radius, 0, 2*Math.PI, true);
	// context.fillStyle = "rgba(112, 161, 255,0.666)";
	// context.fill();
	// context.closePath();

	for( var i=0; i < p_Array_2.length; i++){  //Loop over points
		context.beginPath();
		// context.arc(x,y,r,sAngle,eAngle,counterclockwise);  False = 顺时针，true = 逆时针
		context.arc(xc + p_Array_2[i][0]/scaling_down, yc + p_Array_2[i][1]/scaling_down,radius, 0, 2*Math.PI, true);
		context.fillStyle = "rgba(112, 161, 255,0.666)";
		context.fill();
		context.closePath();
		console.log("- user defined points has been drawn !")
	}

	function drawSrcPoints(){
		if(signal_rotateScene){
			console.log("- drawpoint() robot1_srcArray2 :")
			console.log(robot1_srcArray2);
			for( var i=0; i < robot1_srcArray2.length; i++){  //Loop over points
				context.beginPath();
				// context.arc(x,y,r,sAngle,eAngle,counterclockwise);  False = 顺时针，true = 逆时针
				context.arc(xc + robot1_srcArray2[i][0]/scaling_down, yc + robot1_srcArray2[i][1]/scaling_down,radius, 0, 2*Math.PI, true);
				context.fillStyle = "rgba(255, 165, 2, 0.666)";  // orange
				context.fill();
				context.closePath();
				// robot1_srcArray1 是没有经过视角变换的原始坐标数据
				console.log("- src point has been drawn: " + robot1_srcArray1[i][0] +","+ robot1_srcArray1[i][1])
			}
		}
		else{
			setTimeout(drawSrcPoints, 500)
		}
	}
	
	drawSrcPoints();
	
}



/*****************************************************/
/* Ajax read robot program coordinate Ajax to Django */
/*****************************************************/
function read_robot_coordinates(shop,robot1,robot2){
  	 $.ajax({
	       url:'read_robot_coordinates/',
	       type:'POST',
	       // data:{robotname:{{robotname}}, msgnr:{{msgnr}}, faultspecified:{{faultspecified}},msgkeyword:{{msgkeyword}}, startday:{{startday}},endday:{{endday}},radios:{{radios}} },

	       // the data to post to Django has to be named by "data"
	       data:{"shop":shop,"robot1":robot1, "robot2": robot2},

	       success:function(response){
		     	console.log(response);
		     	robot1_srcObj = response;  // 将读取机器人程序后，后台返回的数据存储下来

		     	// definePointsArrays(response);
		     	// robot1_srcArray1 = []  // init
		     	// robot2_srcArray1 = []  // init
		     	// go through each key in the object
		     	for (const key in response){
		     		let srcname = key
		     		// console.log(srcname)
		     		// console.log(response[srcname]);
		     		for(const key in response[srcname]){
		     			let pointname = key;
		     			// console.log(pointname +" "+ response[srcname][pointname])
		     			robot1_srcArray1.push(response[srcname][pointname])  // 2 add new element
		     		}
		     	}


		     	// 根据生成的robot1_srcArray1构建robot1_srcArray2
		     	robot1_srcArray2 = new Array(robot1_srcArray1.length);
				for( var j=0; j < robot1_srcArray1.length; j++)	//Number of points
				{	
					robot1_srcArray2[j] = new Array(3);		    //Number of dimensions (x,y,z)
				}

				console.log("- Ajax robot1_srcArray1 :")
		     	console.log(robot1_srcArray1);
		     	console.log("- Ajax robot1_srcArray2 :")
		     	console.log(robot1_srcArray2);

		     	signal_defineArrays = true;  // ok for rotateScene()
		     	
		    },
		     error:function(){
	         console.log('failed');
	         alert("Oops! Something wrong !");
	        },

  		})
}



/************************************************************************/
/* rotateScene()														*/
/* Rotates all points in shapeArray2 and puts results in shapeArray2	*/
/* Rotates all points in shadowArray and puts results in shadowArray	*/
/* Rotates all points in gridArray1 and puts results in gridArray2		*/
/* Rotates all points in axisArray1 and puts results in axisArray2		*/
/* Uses rotation matrix S for all of them.								*/
/* 旋转场景（） */
/* 旋转 shapeArray2 中的所有点并将结果放入 shapeArray2 */
/* 旋转 shadowArray 中的所有点并将结果放入 shadowArray */
/* 旋转 gridArray1 中的所有点并将结果放入 gridArray2 */
/* 旋转 axisArray1 中的所有点并将结果放入 axisArray2 */
/* 对所有这些都使用旋转矩阵 S。 */
/************************************************************************/
function rotateScene()
{
	//alert("IN: rotateScene()");
	var tempX, tempY, tempZ;

	/********************************/
	/* Rotate the grid				*/
	/********************************/
	//Array is organized as: gridArray[line][x1,y1,z1,x2,y2,z2] (start point, end point)
	for( var i=0; i < gridArray1.length; i++ )
	{
		//Rotate start point of line i
		gridArray2[i][0] = s11*gridArray1[i][0] + s12*gridArray1[i][1] + s13*gridArray1[i][2];
		gridArray2[i][1] = s21*gridArray1[i][0] + s22*gridArray1[i][1] + s23*gridArray1[i][2];
		gridArray2[i][2] = s31*gridArray1[i][0] + s32*gridArray1[i][1] + s33*gridArray1[i][2];
		//Rotate end point of line i
		gridArray2[i][3] = s11*gridArray1[i][3] + s12*gridArray1[i][4] + s13*gridArray1[i][5];
		gridArray2[i][4] = s21*gridArray1[i][3] + s22*gridArray1[i][4] + s23*gridArray1[i][5];
		gridArray2[i][5] = s31*gridArray1[i][3] + s32*gridArray1[i][4] + s33*gridArray1[i][5];
	}

	/********************************/
	/* Rotate the axes				*/
	/********************************/
	for( var i=0; i< axisArray1.length; i++ )
	{
		for( var j=0; j<axisArray1[0].length; j++ )
		{
			axisArray2[i][j][0] = s11*axisArray1[i][j][0] + s12*axisArray1[i][j][1] + s13*axisArray1[i][j][2];
			axisArray2[i][j][1] = s21*axisArray1[i][j][0] + s22*axisArray1[i][j][1] + s23*axisArray1[i][j][2];
			axisArray2[i][j][2] = s31*axisArray1[i][j][0] + s32*axisArray1[i][j][1] + s33*axisArray1[i][j][2];
		}
	}

	/****************************************/
	/* Rotate the user defined points       */
	/****************************************/
	for( var i=0; i< p_Array_1.length; i++ )
	{
		p_Array_2[i][0] = s11*p_Array_1[i][0] + s12*p_Array_1[i][1] + s13*p_Array_1[i][2];
		p_Array_2[i][1] = s21*p_Array_1[i][0] + s22*p_Array_1[i][1] + s23*p_Array_1[i][2];
		p_Array_2[i][2] = s31*p_Array_1[i][0] + s32*p_Array_1[i][1] + s33*p_Array_1[i][2];
		
	}


	/************************************************/
	/* Rotate robot1 src points (robot1 src points) */
	/************************************************/
	function haha(){
		if(signal_defineArrays == true){
			console.log("rotateScene robot1_srcArray1: ");
			console.log(robot1_srcArray1);
			for( var i=0; i< robot1_srcArray1.length; i++ )
			{
				robot1_srcArray2[i][0] = s11*robot1_srcArray1[i][0] + s12*robot1_srcArray1[i][1] + s13*robot1_srcArray1[i][2];
				robot1_srcArray2[i][1] = s21*robot1_srcArray1[i][0] + s22*robot1_srcArray1[i][1] + s23*robot1_srcArray1[i][2];
				robot1_srcArray2[i][2] = s31*robot1_srcArray1[i][0] + s32*robot1_srcArray1[i][1] + s33*robot1_srcArray1[i][2];
			}
			signal_rotateScene = true;
		}else{
			setTimeout(haha, 500)
		}
	}

	haha();
	
	

	/************************************************/
	/* Rotate robot2 src points (robot2 src points) */
	/************************************************/
	// for( var i=0; i< robot2_srcArray1.length; i++ )
	// {
	// 	robot2_srcArray2[i][0] = s11*robot2_srcArray1[i][0] + s12*robot2_srcArray1[i][1] + s13*robot2_srcArray1[i][2];
	// 	robot2_srcArray2[i][1] = s21*robot2_srcArray1[i][0] + s22*robot2_srcArray1[i][1] + s23*robot2_srcArray1[i][2];
	// 	robot2_srcArray2[i][2] = s31*robot2_srcArray1[i][0] + s32*robot2_srcArray1[i][1] + s33*robot2_srcArray1[i][2];
	// }

	
	console.log("- Finished: rotateScene()");
}



/************************************************************/
/* rotateAxis()	                                            */
/* 自定义旋转坐标轴 & Grid & Points  (后续添加旋转操作按钮使用) */
/************************************************************/
function rotateAxis()
{
	
	/********************************/
	/* Rotate the grid				*/
	/********************************/
	//Array is organized as: gridArray[line][x1,y1,z1,x2,y2,z2] (start point, end point)
	var numLines = 11;		//Number of grid lines in each dimension.  Must be be odd.  This is half the total lines (x & y)
	var pixPerLine = 10;	//Spacing between lines
	var startPix = -pixPerLine*(numLines-1)/2;
	//Create gridArray2 and copy data into it
	gridArray_temp = new Array(numLines*2);
	for( var n=0; n < numLines*2; n++ ){
		gridArray_temp[n]   = new Array(6);
		for( var j=0; j<6; j++ ){
			gridArray_temp[n][j] = gridArray2[n][j];
		}
	}
	for( var i=0; i < gridArray1.length; i++ )
	{
		//Rotate start point of line i
		gridArray_temp[i][0] = r11*gridArray2[i][0] + r12*gridArray2[i][1] + r13*gridArray2[i][2];
		gridArray_temp[i][1] = r21*gridArray2[i][0] + r22*gridArray2[i][1] + r23*gridArray2[i][2];
		gridArray_temp[i][2] = r31*gridArray2[i][0] + r32*gridArray2[i][1] + r33*gridArray2[i][2];
		//Rotate end point of line i
		gridArray_temp[i][3] = r11*gridArray2[i][3] + r12*gridArray2[i][4] + r13*gridArray2[i][5];
		gridArray_temp[i][4] = r21*gridArray2[i][3] + r22*gridArray2[i][4] + r23*gridArray2[i][5];
		gridArray_temp[i][5] = r31*gridArray2[i][3] + r32*gridArray2[i][4] + r33*gridArray2[i][5];
	}
	gridArray2 = gridArray_temp;  // 更新gridArray2
	

	/********************************/
	/* Rotate the Axis				*/
	/********************************/
	axisArray_temp	= new Array(axisArray2.length);
	for( var i=0; i < axisArray2.length; i++ )	//Number of lines
	{		
		axisArray_temp[i] = new Array(axisArray2[i].length);
		for( var j=0; j < axisArray2[i].length; j++)	//Number of points in line
		{	
			axisArray_temp[i][j] = new Array(3);	//Number of dimensions (x,y,z)
		}
	}
	for( var i=0; i < axisArray1.length; i++ ){
		for( var j=0; j < axisArray1[0].length; j++ ){
			axisArray_temp[i][j][0] = r11*axisArray2[i][j][0] + r12*axisArray2[i][j][1] + r13*axisArray2[i][j][2];
			axisArray_temp[i][j][1] = r21*axisArray2[i][j][0] + r22*axisArray2[i][j][1] + r23*axisArray2[i][j][2];
			axisArray_temp[i][j][2] = r31*axisArray2[i][j][0] + r32*axisArray2[i][j][1] + r33*axisArray2[i][j][2];
		}
	}
	axisArray2 = axisArray_temp;  // 更新axisArray2


	/********************************/
	/* Rotate the points     		*/
	/********************************/
}



/************************************************************/
/* computeRotationMatrix()									*/
/* Uses global values of yaw, pitch, roll to compute the	*/
/* rotation matrix.  Populates the global rotation matrix	*/
/* variables, and writes them to the screen.				*/
/* 计算旋转矩阵（） */
/* 使用 yaw、pitch、roll 的全局值来计算 */
/* 旋转矩阵。 填充全局旋转矩阵 */
/* 变量，并将它们写入屏幕。 */
/************************************************************/
function computeRotationMatrix()
{
	//Precompute sine and cosine values
	var su = Math.sin(roll  *Math.PI/180);
	var sv = Math.sin(pitch *Math.PI/180);
	var sw = Math.sin(yaw *Math.PI/180);
	var cu = Math.cos(roll  *Math.PI/180);
	var cv = Math.cos(pitch *Math.PI/180);
	var cw = Math.cos(yaw *Math.PI/180);
	//Compute matrix
	r11 = cv*cw;
	r12 = su*sv*cw - cu*sw;
	r13 = su*sw + cu*sv*cw;
	r21 = cv*sw;
	r22 = cu*cw + su*sv*sw;
	r23 = cu*sv*sw - su*cw;
	r31 = -sv;
	r32 = su*cv;
	r33 = cu*cv;

	//Display Matrix, rounded to three sig. figs.
	// document.getElementById("R11").value = Math.floor(r11*10000)/10000;  // Math.floor() 返回小于或等于一个给定数字的最大整数。
	// document.getElementById("R12").value = Math.floor(r12*10000)/10000;
	// document.getElementById("R13").value = Math.floor(r13*10000)/10000;
	// document.getElementById("R21").value = Math.floor(r21*10000)/10000;
	// document.getElementById("R22").value = Math.floor(r22*10000)/10000;
	// document.getElementById("R23").value = Math.floor(r23*10000)/10000;
	// document.getElementById("R31").value = Math.floor(r31*10000)/10000;
	// document.getElementById("R32").value = Math.floor(r32*10000)/10000;
	// document.getElementById("R33").value = Math.floor(r33*10000)/10000;
}






