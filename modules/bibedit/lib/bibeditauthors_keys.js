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

/********************************************************************
 * Loaded AFTER bibedit_keys.js, overrides some of the default functionality
 * found there.
 *
 ********************************************************************/


/* Handle key return (edit subfield).
 *
 * Since this is a special mode, return also moves to the next field.
 * At the last field of the special mode, it jumps to the first field.
 */
function onKeyReturn(event) {
  var content_cells = $('.bibEditCellContent');
  var current_cell = $(event.target).parent().parent();
  var cur_cell_idx = $(content_cells).index(current_cell);
  var last_content = content_cells.length - 1

  if (event.target.nodeName == 'TEXTAREA') {
    $(event.target).parent().submit();
    if (cur_cell_idx < last_content) {
        $(content_cells).eq(cur_cell_idx + 1).trigger('click');
    } else {
        $(content_cells).eq(0).trigger('click');
    }
    event.preventDefault();
  }

  else if (event.target.nodeName == 'TD') {
    var targetID = event.target.id;
    var type = targetID.slice(0, targetID.indexOf('_'));
    if (type == 'content'){
      $('#' + targetID).trigger('click');
      event.preventDefault();
    }
  }
}

