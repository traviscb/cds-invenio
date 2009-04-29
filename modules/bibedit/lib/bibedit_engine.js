/*
 * This file is part of CDS Invenio.
 * Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 2009 CERN.
 *
 * CDS Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * CDS Invenio is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

/*
 * This is the main BibEdit Javascript.
 */

/*
 * Global variables
 */

// Record data
var gRecID = null;
var gRecord = null;
var gResultSet = null;
// Tag format.
var gTagFormat;
// Is the page dirty?
var gPageDirty = false;

// Highest available field number
var gNewFieldNumber;

// The current hash (fragment part of the URL).
var gHash;
// The current hash deserialized to an object.
var gHashParsed;
// Interval (in ms) between checking if hash has changed.
var gHASH_CHECK_INTERVAL = 250;
// Hash check timer ID.
var gHashCheckTimerID;
// The previous and current state (this is not exactly the same as the state
// parameter, but an internal state control mechanism).
var gPrevState;
var gState;

// Color of new fields.
var gNEW_FIELDS_COLOR = 'lightgreen';
// Duration (in ms) for the color fading of newly added fields.
var gNEW_FIELDS_COLOR_FADE_DURATION = 2000;

window.onload = function(){
  if (typeof(jQuery) == 'undefined'){
    alert('ERROR: jQuery not found!\n\n' +
	  'BibEdit requires jQuery, which does not appear to be installed on ' +
	  'this server. Please alert your site administrator.\n\n' +
	  'Instructions on how to install jQuery and other required plug-ins ' +
	  'can be found in CDS-Invenio\'s INSTALL file.');
    var imgError = document.createElement('img');
    imgError.setAttribute('src', '/img/circle_red.png');
    var txtError = document.createTextNode('jQuery missing');
    var cellIndicator = document.getElementById('cellIndicator');
    cellIndicator.replaceChild(imgError, cellIndicator.firstChild);
    var cellStatus = document.getElementById('cellStatus');
    cellStatus.replaceChild(txtError, cellStatus.firstChild);
  }
};

$(function(){
  /*
   * Initialization of all components when documents is ready.
   */
  initMenu();
  initJeditable();
  initAjax();
  initMisc();
  initStateFromHash();
  gHashCheckTimerID = setInterval(initStateFromHash, gHASH_CHECK_INTERVAL);
  initHotkeys();
});

function initMisc(){
  /*
   * Miscellaneous initialization operations.
   */
  // CERN allows for capital MARC indicators.
  if (gCERNSite)
    validMARC.reIndicator = /[\dA-Za-z]{1}/;

  // Show confirmation dialog when leaving page if content has changed.
  window.onbeforeunload = function(){
    if (gPageDirty)
      return "Your changes have not been submitted.";
  };

  // Add global event handlers.
  $(document).bind('dblclick', function(event){
    onDoubleClick(event);
  });
}

function initAjax(){
  /*
   * Initialize Ajax.
   */
  $.ajaxSetup(
    { cache: false,
      dataType: 'json',
      error: onReqError,
      type: 'POST',
      url: '/record/edit/'
    }
  );
}

function initJeditable(){
  /* Initialize Jeditable with the Autogrow extension. Used for in-place
   * content editing.
   */
  $.editable.addInputType('autogrow', {
    element: function(settings, original){
      var textarea = $('<textarea>');
      if (settings.rows)
        textarea.attr('rows', settings.rows);
      else
        textarea.height(settings.height);
      if (settings.cols)
        textarea.attr('cols', settings.cols);
      else
        textarea.width(settings.width);
      $(this).append(textarea);
      return(textarea);
    },
    plugin: function(settings, original){
      $('textarea', this).autogrow(settings.autogrow);
    }
  });
}

function initStateFromHash(){
  /*
   * Initialize page state from hash.
   */
  if (window.location.hash == gHash)
    // Hash is the same as last time we checked, do nothing.
    return;

  gHash = window.location.hash;
  gHashParsed = (gHash) ? deserializeHash(gHash) : {state: 'edit'};
  gPrevState = gState;
  // Capitalize first letter for later use in eval.
  var state = gHashParsed.state ? gHashParsed.state.charAt(0).toUpperCase() +
    gHashParsed.state.slice(1) : null;
  var recID = gHashParsed.recid;

  // Find out which internal state the new hash leaves us with
  if (state && recID){
    // We have both state and record ID.
    if ($.inArray(state, ['Edit', 'Submit', 'Cancel', 'DeleteRecord']) != -1)
	gState = state;
    else
      // Not a sane state, ignore
      return;
  }
  else if (recID)
    // We only have record ID.
    gState = 'Edit';
  else if (state)
    // We only have state.
    if (state == 'Edit')
      gState = 'StartPage';
    else
      // All states but 'edit' are illegal without record ID, fail...
      return;
  if (gState != gPrevState || (gState == 'Edit' && recID != gRecID)){
    // We have an actual and legal change of state. Do some common cleanup, then
    // call the corresponding event handler.
    updateStatus('updating');
    eval('onStateChangeTo' + gState + '(recID);');
  }
  else
  // What changed was not of interest, continue as if nothing happened.
    return;
}

function deserializeHash(aHash){
  /*
   * Deserializes a string (given as parameter or taken from the window object)
   * into the hash object.
   */
  if (aHash == undefined){
    aHash = window.location.hash;
  }
  var hash = {};
  var args = aHash.slice(1).split('&');
  var tmpArray;
  for (var i=0, n=args.length; i<n; i++){
    tmpArray = args[i].split('=');
    if (tmpArray.length == 2)
      hash[tmpArray[0]] = tmpArray[1];
  }
  return hash;
}

function changeAndSerializeHash(updateData){
  /*
   * Change the hash object to use the data from the object given as parameter.
   * Then update the hash accordingly, WITHOUT invoking initStateFromHash().
   */
  clearTimeout(gHashCheckTimerID);
  gHashParsed = {};
  for (var key in updateData){
    gHashParsed[key.toString()] = updateData[key].toString();
  }
  gHash = '#';
  for (key in gHashParsed){
    gHash += key + '=' + gHashParsed[key] + '&';
  }
  gHash = gHash.slice(0, -1);
  gState = gHashParsed.state.charAt(0).toUpperCase() +
    gHashParsed.state.slice(1);
  window.location.hash = gHash;
  gHashCheckTimerID = setInterval(initStateFromHash, gHASH_CHECK_INTERVAL);
}

function onStateChangeToStartPage(){
  /*
   * Handle change to internal state 'StartPage'.
   */
  cleanUpDisplay();
  disableRecordBrowser();
  $('#txtSearchPattern').val('');
  $('#sctSearchType').val('recID');
  $('#txtSearchPattern').focus();
  updateStatus('ready');
}

function onStateChangeToEdit(recID){
  /*
   * Handle change to internal state 'Edit'.
   */
  $('#txtSearchPattern').val(recID);
  $('#sctSearchType').val('recID');
  onSearchClick();
}

function onStateChangeToSubmit(){
  /*
   * Handle change to internal state 'Submit'.
   */
  cleanUpDisplay();
  $('#txtSearchPattern').val('');
  $('#txtSearchPattern').focus();
  displayMessage('Confirm: Submitted');
  updateStatus('ready');
}

function onStateChangeToCancel(){
  /*
   * Handle change to internal state 'Cancel'.
   */
  cleanUpDisplay();
  disableRecordBrowser();
  $('#txtSearchPattern').val('');
  $('#sctSearchType').val('recID');
  $('#txtSearchPattern').focus();
  updateStatus('ready');
}

function onStateChangeToDeleteRecord(){
  /*
   * Handle change to internal state 'DeleteRecord'.
   */
  cleanUpDisplay();
  disableRecordBrowser();
  $('#txtSearchPattern').val('');
  $('#txtSearchPattern').focus();
  displayMessage('Confirm: Deleted');
  updateStatus('ready');
}

function createReq(data, onSuccess){
  /*
   * Create Ajax request.
   */
  data.ID = createReq.transactionID++;
  $.ajax({
    data: {
      jsondata: JSON.stringify(data)
    },
    success: function(json){
      if (json['resultText'] == 'Error: Not logged in'){
	// User's session has timed out.
	gPageDirty = false;
	window.location = gSiteURL + '/record/' + gRecID + '/edit/';
      }
      onSuccess(json);
    }
  });
}
// Incrementing transaction ID.
createReq.transactionID = 0;

function onReqError(XHR, textStatus, errorThrown){
  /*
   * Handle Ajax request errors.
   */
  alert('Request completed with status ' + textStatus
	+ '\nResult: ' + XHR.responseText
	+ '\nError: ' + errorThrown);
}

function cleanUpDisplay(){
  /*
   * Clears the display and the client side record data.
   */
  deactivateRecordMenu();
  $('#bibEditContent').empty();
  $('.headline').text('BibEdit');
  gRecID = null;
  gRecord = null;
  gPageDirty = false;
}

function notImplemented(event){
  /*
   * Handle unimplemented function.
   */
  alert('Sorry, this function is not implemented yet!');
  event.preventDefault();
}

function onFieldBoxClick(box){
  /*
   * Handle field select boxes.
   */
  // Check/uncheck all subfield boxes, add/remove selected class.
  var rowGroup = $('#rowGroup_' + box.id.slice(box.id.indexOf('_')+1));
  if (box.checked)
    $(rowGroup).find('td[id^=content]').andSelf().addClass('bibEditSelected');
  else
    $(rowGroup).find('td[id^=content]').andSelf().removeClass(
      'bibEditSelected');
  $(rowGroup).find('input[type="checkbox"]').attr('checked', box.checked);
}

function onSubfieldBoxClick(box){
  /*
   * Handle subfield select boxes.
   */
  var tmpArray = box.id.split('_');
  var tag = tmpArray[1], fieldNumber = tmpArray[2], subfieldIndex = tmpArray[3];
  var fieldID = tag + '_' + fieldNumber;
  var subfieldID = fieldID + '_' + subfieldIndex;
  // If uncheck, uncheck field box and remove selected class.
  if (!box.checked){
    $('#content_' + subfieldID).removeClass('bibEditSelected');
    $('#boxField_' + fieldID).attr('checked', false);
    $('#rowGroup_' + fieldID).removeClass('bibEditSelected');
  }
  // If check and all other subfield boxes checked, check field box, add
  // selected class.
  else{
    $('#content_' + subfieldID).addClass('bibEditSelected');
    var field = getFieldFromTag(tag, fieldNumber);
    if (field[0].length == $(
      '#rowGroup_' + fieldID + ' input[type=checkbox]' +
      '[class=bibEditBoxSubfield]:checked').length){
      $('#boxField_' + fieldID).attr('checked', true);
      $('#rowGroup_' + fieldID).addClass('bibEditSelected');
    }
  }
}

function onMoveSubfieldClick(arrow){
  /*
   * Handle subfield moving arrows.
   */
  updateStatus('updating');
  gPageDirty = true;
  var tmpArray = arrow.id.split('_');
  var btnType = tmpArray[0], tag = tmpArray[1], fieldNumber = tmpArray[2],
    subfieldIndex = tmpArray[3];
  var fieldID = tag + '_' + fieldNumber;
  var field = getFieldFromTag(tag, fieldNumber);
  var subfields = field[0];
  var newSubfieldIndex;
  if (btnType == 'btnMoveSubfieldUp')
    newSubfieldIndex = parseInt(subfieldIndex) - 1;
  else
    newSubfieldIndex = parseInt(subfieldIndex) + 1;
  // Create Ajax request.
  var data = {
    recID: gRecID,
    requestType: 'moveSubfield',
    tag: tag,
    fieldNumber: fieldNumber,
    subfieldIndex: subfieldIndex,
    newSubfieldIndex: newSubfieldIndex
  };
  createReq(data, function(json){
    updateStatus('report', json['resultText']);
  });
  // Continue local updating.
  var subfieldToSwap = subfields[newSubfieldIndex];
  subfields[newSubfieldIndex] = subfields[subfieldIndex];
  subfields[subfieldIndex] = subfieldToSwap;
  var rowGroup = $('#rowGroup_' + fieldID);
  var coloredRowGroup = $(rowGroup).hasClass('bibEditFieldColored');
  $(rowGroup).replaceWith(createField(tag, field));
  if (coloredRowGroup)
    $('#rowGroup_' + fieldID).addClass('bibEditFieldColored');
}

function onDoubleClick(event){
  /*
   * Handle double click on editable content fields.
   */
  if (event.target.nodeName == 'TD'){
    var targetID = event.target.id;
    var type = targetID.slice(0, targetID.indexOf('_'));
    if (type == 'content'){
      if (!$(event.target).hasClass('edit_area')){
	// Add event handler for content editing.
	$(event.target).addClass('edit_area').editable(onContentChange, {
	  type: 'autogrow',
	  event: 'dblclick',
	  data: function(){
	    // Get the real content from the record structure (in stead of
	    // from the view, where HTML entities are escaped).
	    var tmpArray = this.id.split('_');
	    var tag = tmpArray[1], fieldNumber = tmpArray[2],
	      subfieldIndex = tmpArray[3];
	    var field = getFieldFromTag(tag, fieldNumber);
	    if (subfieldIndex == undefined)
	      // Controlfield
	      return field[3];
	    else
	      return field[0][subfieldIndex][1];
	  },
	  submit: 'Save',
	  cancel: 'Cancel',
	  placeholder: '',
	  width: '100%',
	  onblur: 'ignore',
	  autogrow: {
	    lineHeight: 16,
	    minHeight: 32
	  }
	}).dblclick();
      }
      event.preventDefault();
    }
  }
}

function onContentChange(value){
  /*
   * Handle 'Save' button in editable content fields.
   */
  updateStatus('updating');
  gPageDirty = true;
  var tmpArray = this.id.split('_');
  var tag = tmpArray[1], fieldNumber = tmpArray[2], subfieldIndex = tmpArray[3];
  var field = getFieldFromTag(tag, fieldNumber);
  value = value.replace(/\n/g, ' '); // Replace newlines with spaces
  if (subfieldIndex == undefined){
    // Controlfield
    field[3] = value;
    subfieldIndex = null;
    var subfieldCode = null;
  }
  else{
    // Regular field
    field[0][subfieldIndex][1] = value;
    var subfieldCode = field[0][subfieldIndex][0];
  }
  // Create Ajax request.
  var data = {
    recID: gRecID,
    requestType: 'modifyContent',
    tag: tag,
    fieldNumber: fieldNumber,
    subfieldIndex: subfieldIndex,
    subfieldCode: subfieldCode,
    value: value
  };
  createReq(data, function(json){
    updateStatus('report', json['resultText']);
  });

  // Return escaped value to display
  return escapeHTML(value);
}

function onAddSubfieldsClick(img){
  /*
   * Handle 'Add subfield' buttons.
   */
  var fieldID = img.id.slice(img.id.indexOf('_')+1);
  var jQRowGroupID = '#rowGroup_' + fieldID;
  if ($('#rowAddSubfieldsControls_' + fieldID).length == 0){
    // The 'Add subfields' form does not exist for this field.
    $(jQRowGroupID).append(createAddSubfieldsForm(fieldID));
    $(jQRowGroupID).data('freeSubfieldTmpNo', 1);
    $('#txtAddSubfieldsCode_' + fieldID + '_' + 0).bind('keyup',
      onAddSubfieldsChange);
    $('#btnAddSubfieldsSave_' + fieldID).bind('click', onAddSubfieldsSave);
    $('#btnAddSubfieldsCancel_' + fieldID).bind('click', function(){
	$('#rowAddSubfields_' + fieldID + '_' + 0).nextAll().andSelf().remove();
    });
    $('#btnAddSubfieldsClear_' + fieldID).bind('click', function(){
      $(jQRowGroupID + ' input[type=text]').val('').removeClass(
	'bibEditInputError');
      $('#txtAddSubfieldsCode_' + fieldID + '_' + 0).focus();
    });
    $('#txtAddSubfieldsCode_' + fieldID + '_' + 0).focus();
  }
  else{
    // The 'Add subfields' form exist for this field. Just add another row.
    var subfieldTmpNo = $(jQRowGroupID).data('freeSubfieldTmpNo');
    $(jQRowGroupID).data('freeSubfieldTmpNo', subfieldTmpNo+1);
    var subfieldTmpID = fieldID + '_' + subfieldTmpNo;
    $('#rowAddSubfieldsControls_' + fieldID).before(
      createAddSubfieldsRow(fieldID, subfieldTmpNo));
    $('#txtAddSubfieldsCode_' + subfieldTmpID).bind('keyup',
      onAddSubfieldsChange);
    $('#btnAddSubfieldsRemove_' + subfieldTmpID).bind('click', function(){
      $('#rowAddSubfields_' + subfieldTmpID).remove();
    });
  }
}

function onAddSubfieldsChange(event){
  /*
   * Validate subfield code and add or remove error class.
   */
  if (this.value.length == 1){
    var valid = validMARC('SubfieldCode', this.value);
    if (!valid && !$(this).hasClass('bibEditInputError'))
      $(this).addClass('bibEditInputError');
    else if (valid && $(this).hasClass('bibEditInputError'))
      $(this).removeClass('bibEditInputError');
  }
  else if ($(this).hasClass('bibEditInputError'))
    $(this).removeClass('bibEditInputError');
}

function onAddSubfieldsSave(event){
  /*
   * Handle 'Save' button in add subfields form.
   */
  updateStatus('updating');
  var tmpArray = this.id.split('_');
  var tag = tmpArray[1], fieldNumber = tmpArray[2];
  var fieldID = tag + '_' + fieldNumber;
  var subfields = [];
  var protectedSubfield = false, invalidOrEmptySubfields = false;
  // Collect valid fields in an array.
  $('#rowGroup_' + fieldID + ' .bibEditTxtSubfieldCode'
   ).each(function(){
     var MARC = getMARC(tag, fieldNumber) + this.value;
     if ($.inArray(MARC, gProtectedFields) != -1){
       protectedSubfield = MARC;
       return false;
     }
     var subfieldTmpNo = this.id.slice(this.id.lastIndexOf('_')+1);
     var txtValue = $('#txtAddSubfieldsValue_' + fieldID + '_' +
       subfieldTmpNo);
     var value = $(txtValue).val();
     if (!$(this).hasClass('bibEditInputError')
	 && this.value != ''
	 && !$(txtValue).hasClass('bibEditInputError')
	 && value != '')
       subfields.push([this.value, value]);
     else
       invalidOrEmptySubfields = true;
  });

  if (protectedSubfield){
    displayAlert('alert', 'errorAddProtectedSubfield', true);
    return;
  }
  if (invalidOrEmptySubfields && !displayAlert('confirm',
					       'warningInvalidOrEmptyInput')){
    updateStatus('ready');
    return;
  }

  if (!subfields.length == 0){
    gPageDirty = true;
    // Create Ajax request
    var data = {
      recID: gRecID,
      requestType: 'addSubfields',
      tag: tag,
      fieldNumber: fieldNumber,
      subfields: subfields
    };
    createReq(data, function(json){
      updateStatus('report', json['resultText']);
    });

    // Continue local updating
    var field = getFieldFromTag(tag, fieldNumber);
    field[0] = field[0].concat(subfields);
    var rowGroup  = $('#rowGroup_' + fieldID);
    var coloredRowGroup = $(rowGroup).hasClass('bibEditFieldColored');
    $(rowGroup).replaceWith(createField(tag, field));
    if (coloredRowGroup)
      $('#rowGroup_' + fieldID).addClass('bibEditFieldColored');

    // Color the new fields for a short period.
    var rows = $('#rowGroup_' + fieldID + ' tr');
    $(rows).slice(rows.length - subfields.length).effect(
      'highlight', {color: gNEW_FIELDS_COLOR}, gNEW_FIELDS_COLOR_FADE_DURATION);
  }
  else{
    // No valid fields were submitted.
    $('#rowAddSubfields_' + fieldID + '_' + 0).nextAll().andSelf().remove();
    updateStatus('ready');
  }
}

function onDeleteFields(event){
  /*
   * Handle 'Delete selected' button or delete hotkeys.
   */
  updateStatus('updating');
  var toDelete = {};
  // Collect and remove all marked fields.
  var checkedFieldBoxes = $('input[class="bibEditBoxField"]:checked');
  $(checkedFieldBoxes).each(function(){
    var tmpArray = this.id.split('_');
    var tag = tmpArray[1], fieldNumber = tmpArray[2];
    if (!toDelete[tag]){
      toDelete[tag] = {};
    }
    toDelete[tag][fieldNumber] = [];
  });
  // Collect subfields to be deleted in a datastructure.
  var checkedSubfieldBoxes = $('input[class="bibEditBoxSubfield"]:checked');
  $(checkedSubfieldBoxes).each(function(){
    var tmpArray = this.id.split('_');
    var tag = tmpArray[1], fieldNumber = tmpArray[2],
      subfieldIndex = tmpArray[3];
    if (!toDelete[tag]){
      toDelete[tag] = {};
      toDelete[tag][fieldNumber] = [subfieldIndex];
    }
    else{
      if (!toDelete[tag][fieldNumber])
	toDelete[tag][fieldNumber] = [subfieldIndex];
      else if (toDelete[tag][fieldNumber].length == 0)
	// Entire field scheduled for the deletion.
	return;
      else
	toDelete[tag][fieldNumber].push(subfieldIndex);
    }
  });
  var fieldsDeleted = Boolean(checkedFieldBoxes.length);

  if (!fieldsDeleted && !checkedSubfieldBoxes.length){
    // No field/subfields selected.
    if (event.type == 'keydown' && event.target.nodeName == 'TD'){
      // Delete focused field/subfield.
      var targetID = event.target.id;
      var tmpArray = targetID.split('_');
      if (tmpArray[0] == 'content'){
	var tag = tmpArray[1], fieldNumber = tmpArray[2],
	  subfieldIndex = tmpArray[3];
	toDelete[tag] = {};
	if (event.shiftKey){
	  toDelete[tag][fieldNumber] = [];
	  fieldsDeleted = true;
	}
	else
	  toDelete[tag][fieldNumber] = [subfieldIndex];
      }
    }
    else{
      // Not a valid deletion event.
      updateStatus('ready');
      return;
    }
  }

  // Assert that no protected fields are scheduled for deletion.
  var protectedField = containsProtectedField(toDelete);
  if (protectedField){
    displayAlert('alert', 'errorDeleteProtectedField', true, protectedField);
    return;
  }

  gPageDirty = true;
  // Create Ajax request.
  var data = {
    recID: gRecID,
    requestType: 'deleteFields',
    toDelete: toDelete
  };
  createReq(data, function(json){
    updateStatus('report', json['resultText']);
  });

  /* Continue local updating.
  Parse datastructure and delete accordingly in record, then redraw
  fields that had subfields deleted. */
  var fieldNumbersToDelete, subfieldIndexesToDelete, field, subfields,
    subfieldIndex;
  for (var tag in toDelete){
    fieldNumbersToDelete = toDelete[tag];
    for (var fieldNumber in fieldNumbersToDelete){
      var fieldID = tag + '_' + fieldNumber;
      subfieldIndexesToDelete = fieldNumbersToDelete[fieldNumber];
      if (subfieldIndexesToDelete.length == 0){
	deleteFieldFromTag(tag, fieldNumber);
	$('#rowGroup_' + tag + '_' + fieldNumber).remove();
      }
      else{
	subfieldIndexesToDelete.sort();
	field = getFieldFromTag(tag, fieldNumber);
	subfields = field[0];
	for (var j=subfieldIndexesToDelete.length-1; j>=0; j--)
	  subfields.splice(subfieldIndexesToDelete[j], 1);
	var rowGroup = $('#rowGroup_' + fieldID);
	if (!fieldsDeleted){
	  // Color subfield after updating.
	  var coloredRowGroup = $(rowGroup).hasClass('bibEditFieldColored');
	  $(rowGroup).replaceWith(createField(tag, field));
	  if (coloredRowGroup)
	    $('#rowGroup_' + fieldID).addClass( 'bibEditFieldColored');
	}
	else
	  $(rowGroup).replaceWith(createField(tag, field));
      }
    }
  }
  if (fieldsDeleted)
    // If entire fields has been deleted, recolor the full table.
    reColorFields();
  resetNewFieldNumber();
}

function colorFields(){
  /*
   * Color every other field (rowgroup) gray to increase readability.
   */
  $('#bibEditTable tbody:even').each(function(){
    $(this).addClass('bibEditFieldColored');
  });
}

function reColorFields(){
  /*
   * Update coloring by removing existing, then recolor.
   */
  $('#bibEditTable tbody').each(function(){
    $(this).removeClass('bibEditFieldColored');
  });
  colorFields();
}

function getTagsSorted(){
  /*
   * Return field tags in sorted order.
   */
  var tags = [];
  for (var tag in gRecord){
    tags.push(tag);
  }
  return tags.sort();
}

function getMARC(tag, fieldNumber, subfieldIndex){
  /*
   * Return the MARC representation of a field or a subfield.
   */
  var field = getFieldFromTag(tag, fieldNumber);
  var ind1, ind2;
  if (tag < 10)
    ind1 = '', ind2 = '';
  else{
    ind1 = (field[1] == ' ' || !field[1]) ? '_' : field[1];
    ind2 = (field[2] == ' ' || !field[2]) ? '_' : field[2];
  }
  if (subfieldIndex == undefined)
    return tag + ind1 + ind2;
  else
    return tag + ind1 + ind2 + field[0][subfieldIndex][0];
}

function getFieldFromTag(tag, fieldNumber){
  /*
   * Get a specified field.
   */
  var fields = gRecord[tag];
  var field;
  for (var i=0, n=fields.length; i<n; i++){
    field = fields[i];
    if (fieldNumber == field[4])
      break;
  }
  return field;
}

function deleteFieldFromTag(tag, fieldNumber){
  /*
   * Delete a specified field.
   */
  var field = getFieldFromTag(tag, fieldNumber);
  var fields = gRecord[tag];
  fields.splice($.inArray(field, fields), 1);
  // If last field, delete tag.
  if (fields.length == 0){
    delete gRecord[tag];
  }
}

function cmpFields(field1, field2){
  /*
   * Compare fields by indicators (tag assumed equal).
   */
  if (field1[1].toLowerCase() > field2[1].toLowerCase())
    return 1;
  else if (field1[1].toLowerCase() < field2[1].toLowerCase())
    return -1;
  else if (field1[2].toLowerCase() > field2[2].toLowerCase())
    return 1;
  else if (field1[1].toLowerCase() < field2[1].toLowerCase())
    return -1;
  return 0;
}

function resetNewFieldNumber(){
  /*
   * Reset first available field number.
   */
  var existingNumbers = [];
  var fields, field;
  for (var tag in gRecord){
    fields = gRecord[tag];
    for (var i=0, n=fields.length; i<n; i++){
      existingNumbers.push(fields[i][4]);
    }
  }
  existingNumbers.sort(function (a,b){ return a-b; });
  gNewFieldNumber = existingNumbers.pop() + 1;
}

function validMARC(datatype, value){
  /*
   * Validate a value of given datatype according to the MARC standard. The
   * value should be restricted/extended to it's expected size before being
   * passed to this function.
   * Datatype can be 'ControlTag', 'Tag', 'Indicator' or 'SubfieldCode'.
   * Returns a boolean.
   */
  return eval('validMARC.re' + datatype + '.test(value)');
}
// MARC validation REs
validMARC.reControlTag = /00[1-9A-Za-z]{1}/;
validMARC.reTag = /(0([1-9A-Z][0-9A-Z])|0([1-9a-z][0-9a-z]))|(([1-9A-Z][0-9A-Z]{2})|([1-9a-z][0-9a-z]{2}))/;
validMARC.reIndicator = /[\da-z]{1}/;
validMARC.reSubfieldCode = /[\da-z!&quot;#$%&amp;'()*+,-./:;&lt;=&gt;?{}_^`~\[\]\\]{1}/;

function getFieldTag(MARC){
  /*
   * Get the tag name of a field in format as specified by gTagFormat.
   */
  MARC = MARC.substr(0, 5);
  if (gTagFormat == 'human'){
    var tagName = gTagNames[MARC];
    if (tagName != undefined)
      // Direct hit. Return it.
      return tagName;
    else{
      // Start looking for wildcard hits.
      if (MARC.length == 3){
	// Controlfield
	tagName = gTagNames[MARC.substr(0, 2) + '%'];
	if (tagName != undefined && tagName != MARC + 'x')
	  return tagName;
      }
      else{
	// Regular field, try finding wildcard hit by shortening expression
	// gradually. Ignores wildcards which gives values like '27x'.
	var term = MARC + '%', i = 5;
	do{
	  tagName = gTagNames[term];
	  if (tagName != undefined){
	    if (tagName != MARC.substr(0, i) + 'x')
	      return tagName;
	    break;
	  }
	  i--;
	  term = MARC.substr(0, i) + '%';
	}
	while (i >= 3)
      }
    }
  }
  return MARC;
}

function getSubfieldTag(MARC){
  /*
   * Get the tag name of a subfield in format as specified by gTagFormat.
   */
  if (gTagFormat == 'human'){
    var subfieldName = gTagNames[MARC];
      if (subfieldName != undefined)
	return subfieldName;
      else{
	// Look for standardized abbrevs for subfields
        var term = '%%%%%' + MARC.charAt(5);
	subfieldName = gTagNames[term];
        if (subfieldName != undefined)
	  return subfieldName;
       }
  }
  return '$$' + MARC.charAt(5);
}

function fieldIsProtected(MARC){
  /*
   * Determine if a MARC field is protected or part of a protected group of
   * fields.
   */
  do{
    var i = MARC.length - 1;
    if ($.inArray(MARC, gProtectedFields) != -1)
      return true;
    MARC = MARC.substr(0, i);
    i--;
  }
  while (i >= 1)
  return false;
}

function containsProtectedField(fieldData){
  /*
   * Determine if a field data structure contains protected elements (useful
   * when checking if a deletion command is valid).
   * The data structure must be an object with the following levels
   * - Tag
   *   - Field number
   *     - Subfield index
   */
  var fieldNumbers, subfieldIndexes, MARC;
  for (var tag in fieldData){
    fieldNumbers = fieldData[tag];
    for (var fieldNumber in fieldNumbers){
      subfieldIndexes = fieldNumbers[fieldNumber];
      if (subfieldIndexes.length == 0){
	MARC = getMARC(tag, fieldNumber);
	if (fieldIsProtected(MARC))
	  return MARC;
	}
      else{
	for (var i=0, n=subfieldIndexes.length; i<n; i++){
	  MARC = getMARC(tag, fieldNumber, subfieldIndexes[i]);
	  if (fieldIsProtected(MARC))
	    return MARC;
	}
      }
    }
  }
  return false;
}