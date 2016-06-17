var url = '';
$(document).ready(function(){
	retriveProject();

	$("#default-option").change(function(){
		var project = $("#default-option").val();
		if(project!='')
			retriveActiveHosts(project);
	});

	$('#hostsTable').on('click','.activation-btn',function () {
		var project = $("#default-option").val();
		if ($(this).hasClass("btn-danger")) {
			var hostIp = $('#host-ip').text();
			var portIp = $('#port-ip').text();
			var host = encodeURI(hostIp+':'+portIp);
			sendActiveHosts(this);
		}
	});

	$('#sample1 input').ptTimeSelect();

});

var rowCount = 1;
function addMoreRows(frm) {
	rowCount ++;
	var recRow = '<tr id="rowCount'+rowCount+'">' +
		'<td class="vMiddle first-child">' +
		'<input type="text" placeholder="255.255.255.255:port" name="hostInput"/>' +
		'</td>' +
		'<td class="vMiddle">' +
		'<div>' +
		'<button type="button" class="btn btn-danger activation-btn">Inactive</button>'+
		'<td class="vMiddle text-right">' +
		'<a href="javascript:void(0);" class="greenText mr15" onclick="addNewHost()">' +'apply</a>' +
		'<a href="javascript:void(0);" class="redText" onclick="removeRow('+rowCount+');">remove</a>' +
		'</td>' +
		'</tr>';
	$('#hostsTable').find('tr:last').before(recRow);
}

var rowCount2 = 100;
function addMoreRows2(frm) {
	rowCount2 ++;
	var recRow =
		'<tr id="rowCount'+rowCount2+'">' +
		'<td class="vMiddle">' +
		'<input type="text" name="commandName" placeholder="task name"/>' +
		'</td>' +
		'<td class="vMiddle text-center">' +
		'<table>' +
		'<tr>' +
		'<td class="tinyTd">' +
		'<span class="tinyText">Min</span>' +
		'<input class="text-center" name="min" type="text" value="15"/>' +
		'</td>' +
		'<td class="tinyTd">' +
		'<span class="tinyText">Hr</span>' +
		'<input class="text-center" name="hr" type="text" value="18"/>' +
		'</td> ' +
		'<td class="tinyTd">' +
		'<span class="tinyText">Dom</span>' +
		'<input class="text-center" name="dom" type="text" value="*"/>' +
		'</td>' +
		'<td class="tinyTd">' +
		'<span class="tinyText">Mon</span>' +
		'<input class="text-center" name="mon" type="text" value="*"/>' +
		'</td>' +
		'<td class="tinyTd">' +
		'<span class="tinyText">DoW</span>' +
		'<input class="text-center" name="doW" type="text" value="Sat"/>' +
		'</td>' +
		'</tr>' +
		'</table>' +
		'</td>' +
		'<td class="vMiddle">' +
		'<input type="text" name="command" placeholder="Command"/>' +
		'</td>' +
		'<td class="vMiddle">' +
		'<input type="text" name="description" placeholder="Description"/>' +
		'</td>'+
		'<td class="vMiddle text-right">' +
		'<a href="javascript:" class="greenText inline mr15" id="command-ajax" onclick="commandAjax(this)">apply</a>' +
		'<a href="javascript:" class="redText inline mr15" onclick="removeRow2(rowCount2)">cancel</a>' +
		'</td>' +
		'</tr>';
	$('#cron').find('tr:last').before(recRow);
}


//ajax Get requests
function retriveProject(){
	$.ajax({
		url: url+'/projects',
		type: 'GET',
		dataType: 'json',
		complete: function (response) {
			var projectsNames = jQuery.parseJSON(response.responseText);
			var size          = countPropertiesForProject(projectsNames);
			var defultOption  = $('#default-option');
			defultOption.append(
				'<option value="">'+"Select project"+'</option>'
			);
			for(var count=0;count<size;count++) {
				$('#default-option').append(
					'<option value="'+projectsNames[count]['name']+'">' +
					projectsNames[count]['name']
					+'</option>'
				);
			}
			var url         = window.location.href;
			var projectName =url.split('?');
			defultOption.val(projectName[1]).change();
		}
	});

	return false;
}

function retriveActiveHosts(project){
	$.ajax({
		url: url+'/activehost?project='+project,
		type: 'GET',
		dataType: 'json',
		complete: function (response) {
			var activeHost = jQuery.parseJSON(response.responseText);
			retrieveHosts(project,activeHost['active_host']);
			retrieveCommands(project);
		}
	});

	return false;
}

function addProjectPopup(){
	$('#addProject').modal('show');

	return false;
}

function addProject(){
	var projectName = $("input[name='prjectName']").val();
	var userName    = $("input[name='userName']").val();

	$.ajax({
		url: url+'/addproject?name='+projectName+'&user='+userName,
		type: 'GET',
		dataType: 'json',
		complete: function (response) {
			var responseStatus = jQuery.parseJSON(response.responseText)
			if(responseStatus.status=='failed, name already exist') {
				$('#project-name-span').text('project name already exist');
				return false;
			}
			$('#addProject').modal('hide');
			window.location.href = '/index.html?';

		}
	});

	return false;
}

function retrieveHosts(project,activeHost){
	$.ajax({
		url:url+'/hosts?project='+project,
		type: 'GET',
		dataType: 'json',
		complete: function (response) {
			var hostPort = $('.host-port');
			if(hostPort.is(':visible')) {
				hostPort.remove();
			}
			var hosts = jQuery.parseJSON(response.responseText);
			var size= countProperties(hosts);
			var className;
			var activationStatus;
			var host;
			for(var count=0;count<size;count++) {
				className = 'btn-danger';
				activationStatus = 'Inactive';
				if(activeHost===hosts[count]) {
					className = 'btn-success';
					activationStatus = 'Active';
				}
				host = hosts[count].split(":");
				$('#hosts').after(
					'<tr class="host-port">' +
					'<td class="vMiddle first-child" id="hosts">' +
					'<span class="bold" id="host-ip">'+host[0]+'</span>'+":"+
					'<span class="bold greenText" id="port-ip">'+host[1]+'</span>' +
					'</td>' +
					'<td class="vMiddle">' +
					'<div>' +
					'<button type="button" id="'+host[0]+':'+host[1]+'" class="btn activation-btn '+className+'">'+activationStatus+'</button>'+
					'<td class="vMiddle text-right">' +
					'<a href="javascript:" class="redText" onclick="removeHost(\'' + project+ '\' ,\'' +  hosts[count]+ '\');">remove</a>' +
					'</td>'
				);

			}
		}

	});

	return false;
}


function retrieveCommands(project){
	$.ajax({
		url: url+'/crons?project='+project,
		type: 'GET',
		dataType: 'json',
		complete: function (response) {
			compelteAjax(response);
		}
	});

	return false;
}

function removeCommand(elem) {
	var project = $("#default-option").val();
	$.ajax({
		url: url+'/delcron?project='+project+'&task='+elem.id,
		type: 'GET',
		dataType: 'json',
		complete: function (response) {
			window.location.href='/index.html?'+project;
		}
	});

	return false;
}

function search() {
	var project  = $("#default-option").val();
	var name     = $("input[name='searchName']").val();
	var dateFrom = $("input[name='s1Time1']").val();
	var dateTo   = $("input[name='s1Time2']").val();

	if($('.command-dev').is(':visible')) {
		$('.command-dev').remove();
	}

	dateFrom  = dateFrom.split(' ');
	dateTo    = dateTo.split(' ');
	var startDate='';
	var endDate='';
	var hours;
	var min;

	if(dateFrom!='')
		startDate = dateFrom[0]+':00';
	if(dateTo!='')
		endDate   = dateTo[0]+':00';

	if(dateFrom[1]=='PM' && parseInt(dateFrom[0].split(':')[0])<12){
		hours = parseInt(dateFrom[0].split(':')[0]) + 12;
		min = dateFrom[0].split(':')[1];
		startDate = hours + ':' + min + ':00';
	}else if(dateFrom[1]=='AM' && parseInt(dateFrom[0].split(':')[0])==12) {
		hours = '00';
		min = dateFrom[0].split(':')[1];
		startDate = hours + ':' + min + ':00';
	}

	if(dateTo[1]=='PM' && parseInt(dateTo[0].split(':')[0])<12){
		hours = parseInt(dateTo[0].split(':')[0])+12;
		min   = dateTo[0].split(':')[1];
		endDate = hours+':'+min+':'+59;
	}else if(dateTo[1]=='AM' && parseInt(dateTo[0].split(':')[0])==12){
		hours = '00';
		min = dateTo[0].split(':')[1];
		endDate = hours + ':' + min + ':00';
	}

	$.ajax({
		url: url+'/searchcron',
		type: 'GET',
		dataType: 'json',
		data: {project: project,namelike:name,from:startDate,to:endDate},
		complete: function (response) {
			compelteAjax(response);
		}
	});

	return false;
}

function editCron(OldcommandName,count) {
	var commandName = $("input[name='editCommandName"+count+"']").val().trim();
	var editMin     = $("input[name='editMin"+count+"']").val();
	var editHr      = $("input[name='editHr"+count+"']").val();
	var editDom     = $("input[name='editDom"+count+"']").val();
	var editMon     = $("input[name='editMon"+count+"']").val();
	var editDow     = $("input[name='editDow"+count+"']").val();
	var command     = $("input[name='command"+count+"']").val();
	var description = $("input[name='description"+count+"']").val();
	var project     = $("#default-option").val();
	var time        = editMin+' '+editHr+' '+editDom+' '+editMon+' '+editDow;
	var setString;
	var valueString;
	if(OldcommandName!=commandName) {
		setString  = 'name,time,command,description';
		valueString = commandName+','+time+','+command+','+description;
	}
	else {		
		setString = 'time,command,description';
		valueString =time + ',' + command + ',' + description;
	}
	$.ajax({
		url: url+'/editcron',
		type: 'GET',
		dataType: "json",
		contentType: "application/json",
		data: {task: OldcommandName,set:setString,to:valueString},
		complete: function (response) {
			window.location.href='/index.html?'+project;
		}
	});

	return false;
}
function removeHost(project,host) {
	$.ajax({
		url: url+'/delhost',
		type: 'GET',
		dataType: "json",
		contentType: "application/json",
		data: {project: project,host:host},
		complete: function (response) {
			window.location.href='/index.html?'+project;
		}

	});

	return false;
}

function addCommandView() {
	var project = $("#default-option").val();
	$.ajax({
		url: url+'/generate?project='+project+'&update=0',
		type: 'GET',
		dataType: 'json',
		complete: function (response) {
			$('.commandView').is(':visible')
			{
				$('.commandView').remove();
			}
			$('#command-view').append("<pre class='commandView'>"+response.responseText+"</pre>");
		}
	});

	return false;
}

function brodcast() {
	var project = $("#default-option").val();
	$.ajax({
		url: url + '/generate?project=' + project + '&update=1',
		type: 'GET',
		dataType: 'json',
		complete :function( jqXHR, textStatus ) {
			$('#showModal').modal('hide');
		}
	});

}
//ajax POST requests
function sendActiveHosts(elem) {
	var project = $("#default-option").val();
	$.ajax({
		url: url+'/activate_host',
		type: 'GET',
		dataType: "json",
		contentType: "application/json",
		data: {project: project,host:elem.id},
		complete: function (response) {
			window.location.href='/index.html?'+project;
		}
	});

	return false;
}

function addNewHost() {
	var host    = encodeURI($("input[name='hostInput']").val());
	var project = $("#default-option").val();
	$.ajax({
		url: url+'/addhost',
		type: 'GET',
		dataType: "json",
		contentType: "application/json",
		data: {project: project,host:host},
		success: function (response) {
			window.location.href='/index.html?'+project;
		}

	});

	return false;
}


function brodcastConfirmation() {
	$('#showModal').modal('show');
}

function editCommand(elem) {
	var elemClass = elem.id;
	$("."+elemClass).removeClass("hide");
	$("#"+elemClass).hide();

	return false;
}

function cancel(elem) {
	var elemClass = elem.id;
	$("."+elemClass).addClass("hide");
	$("#"+elemClass).show();

	return false;
}

function commandAjax(elem) {
	var commandName  = $("input[name='commandName']").val();
	var min          = $("input[name='min']").val();
	var hr           = $("input[name='hr']").val();
	var dom          = $("input[name='dom']").val();
	var mon          = $("input[name='mon']").val();
	var dow          = $("input[name='doW']").val();
	var command      = $("input[name='command']").val();
	var description  = $("input[name='description']").val();
	var project      = $("#default-option").val();
	var time         = min+' '+hr+' '+dom+' '+mon+' '+dow;

	$.ajax({
		url: url+'/addcron',
		type: 'POST',
		dataType: "json",
		contentType: "application/json",
		data: {task: commandName.trim(),time:time,command:command.trim(),project:project,description:description},
		complete: function (response) {
			$("#default-option").val(project);
			window.location.href='/index.html?'+project;
		}
	});

	return false;
}

function removeRow2(removeNum) {
	$('#rowCount'+removeNum).remove();
}

function removeRow(removeNum) {
	$('#rowCount'+removeNum).remove();
}

function countProperties(obj) {
	var prop;
	var propCount = 0;
	for (prop in obj) {
		propCount++;
	}
	return propCount;
}

function countPropertiesForCommand(obj) {
	var prop='command';
	var propCount = 0;

	for (prop in obj) {
		propCount++;
	}
	return propCount;
}

function countPropertiesForProject(obj) {
	var prop='name';
	var propCount = 0;

	for (prop in obj) {
		propCount++;
	}
	return propCount;
}


function compelteAjax(response) {
	if($('.command-dev').is(':visible'))
		$('.command-dev').remove();

	var commands = jQuery.parseJSON(response.responseText);
	var size    = countPropertiesForCommand(commands);
	var src;
	for(var count=0;count<size;count++) {
		var date = new Date(commands[count]['last_run_at'].$date);
		date     = date.setHours(date.getHours() - 3);
		date     = new Date(date);
		var time  = commands[count]['time'].split(' ');
		src       = "images/true-symbole.png";
		if(commands[count]['last_run_status']!=0)
			src   = "images/wrong.jpeg";

		$('#commands').after(
			'<tr class="command-dev" id="command-dev'+count+'"">' +
			'<td class="vMiddle" title="'+commands[count]['description']+'"><span class="bold">'+commands[count]['name']+'</span></td>' +
			'<td class="vMiddle">' +
			'<table>' +
			'<tr>' +
			'<td class="tinyTd"><span class="tinyText">Min</span><span class="blackText">'+time[0]+'</span></td>' +
			'<td class="tinyTd"><span class="tinyText">Hr</span><span class="blackText">'+time[1]+'</span></td>' +
			'<td class="tinyTd"><span class="tinyText">Dom</span><span class="blackText">'+time[2]+'</span></td>' +
			'<td class="tinyTd"><span class="tinyText">Mon</span><span class="blackText">'+time[3]+'</span></td>' +
			'<td class="tinyTd"><span class="tinyText">DoW</span><span class="blackText">'+time[4]+'</span></td>' +
			'</tr>' +
			'</table>' +
			'</td>' +
			'<td class="vMiddle" colspan="2">' +
			'<span>'+commands[count]['command']+'</span>' +
			'</td>' +
			'<td class="vMiddle text-center">' +
			'<img src="'+src+'" alt="Smiley face" height="25" width="25">'+
			'</td>' +
			'<td class="vMiddle text-center">' +
			'<a href="#" class="blueText">'+date.toString()+'</a>' +
			'</td>' +
			'<td class="vMiddle text-center">' +
			'<a href="javascript:void(0);" class="blueText" onclick="editCommand(this);" id="command-dev'+count+'"">edit</a>' +
			'</td>' +
			'</td>' +
			'<td class="vMiddle text-right">' +
			'<a href="javascript:" class="redText" onclick="removeCommand(this)" id="'+commands[count]['name']+'">remove</a>' +
			'</td>'+
			'<tr id="rowCount'+rowCount2+'" class="hide command-dev'+count+'"><td class="vMiddle">' +
			'<input type="text" value="'+commands[count]['name']+'" name="editCommandName'+count+'" placeholder="task name"/></td>' +
			'<td class="vMiddle text-center">' +
			'<table>' +
			'<tr>' +
			'<td class="tinyTd">' +
			'<span class="tinyText">Min</span>' +
			'<input class="text-center" name="editMin'+count+'" type="text" value="'+time[0]+'"/>' +
			'</td>' +
			'<td class="tinyTd">' +
			'<span class="tinyText">Hr</span>' +
			'<input class="text-center" name="editHr'+count+'" type="text" value="'+time[1]+'"/>' +
			'</td> ' +
			'<td class="tinyTd">' +
			'<span class="tinyText">Dom</span>' +
			'<input class="text-center" name="editDom'+count+'" type="text" value="'+time[2]+'"/>' +
			'</td>' +
			'<td class="tinyTd">' +
			'<span class="tinyText">Mon</span>' +
			'<input class="text-center" name="editMon'+count+'" type="text" value="'+time[3]+'"/>' +
			'</td>' +
			'<td class="tinyTd">' +
			'<span class="tinyText">DoW</span>' +
			'<input class="text-center" name="editDow'+count+'" type="text" value="'+time[4]+'"/>' +
			'</td>' +
			'</tr>' +
			'</table>' +
			'</td>' +
			'<td class="vMiddle">' +
			'<input type="text" name="command'+count+'" value="'+commands[count]['command']+'"/>' +
			'</td>' +
			'<td class="vMiddle">' +
			'<input type="text" value="'+commands[count]['description']+'" name="description'+count+'" placeholder="description"/></td>' +
			'</td>' +
			'<td class="vMiddle text-right">' +
			'<a href="javascript:" class="greenText inline mr15" id="command-ajax" onclick="editCron(\'' + commands[count]['name'] + '\' , \'' + count + '\')">apply</a>' +
			'<a href="javascript:void(0);" class="redText inline mr15" id="command-dev'+count+'" onclick="cancel(this);">cancel</a>' +
			'</td></tr>'
		);
	}
}