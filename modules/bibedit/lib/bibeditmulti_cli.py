#!/usr/bin/env python
# -*- coding: utf-8 -*-
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CDS Invenio Multiple Record Editor command-line interface."""

import sys, os
import optparse

import invenio.messages 
from invenio.config import CFG_SITE_LANG

from invenio.webinterface_handler import WebInterfaceDirectory, \
                                         wash_urlargd
from invenio.webpage import page
from invenio import bibeditmulti_engine as multi_edit_engine

from invenio.webuser import page_not_authorized
from invenio.access_control_engine import acc_authorize_action

class _ActionTypes:
    """Define the available action types"""
    test_search = "testSearch"
    display_detailed_record = "displayDetailedRecord"
    preview_results = "previewResults"
    display_detailed_result = "displayDetailedResult"
    submit_changes = "submitChanges"

    def __init__(self):
        """Nothing to init"""
        pass

class _FieldActionTypes:
    """Define the available action types"""
    add = "0"
    delete = "1"
    update = "2"

    def __init__(self):
        """Nothing to init"""
        pass

class _SubfieldActionTypes:
    """Define the available action types"""
    add = "0"
    delete = "1"
    replace_content = "2"
    replace_text = "3"

    def __init__(self):
        """Nothing to init"""
        pass

class EXAMPLE_USAGE_FROM_WEB:
    """Defines the set of /multiedit pages."""

    _exports = [""]

    _action_types = _ActionTypes()

    _field_action_types = _FieldActionTypes()
    _subfield_action_types = _SubfieldActionTypes()


    def process_update_request(self, language, search_criteria, current_record_id,
                                    commands, output_format, page_to_display ):

        if action_type == self._action_types.preview_results:
            commands_list = self._create_commands_list(commands)
            return multi_edit_engine.perform_request_test_search(
                                                    search_criteria,
                                                    commands_list,
                                                    output_format,
                                                    page_to_display,
                                                    language)

        if action_type == self._action_types.submit_changes:
            commands_list = self._create_commands_list(commands)
            return multi_edit_engine.perform_request_submit_changes(
                                                    search_criteria, 
                                                    commands_list, language)

        # In case we obtain wrong action type we return empty page.
        return " "

    def _create_subfield_commands_list(self, subfields):
        """Creates the list of commands for the given subfields.

        @param subfields: json structure containing information about
        the subfileds. This data is used for creating the commands.

        @return: list of subfield commands.
        """
        commands_list = []

        for current_subfield in subfields:

            action = current_subfield["action"]
            subfield_code = current_subfield["subfieldCode"]
            value = current_subfield["value"]
            new_value = current_subfield["newValue"]

            if action == self._subfield_action_types.add:
                subfield_command = multi_edit_engine.AddSubfieldCommand(subfield_code, value)
            elif action == self._subfield_action_types.delete:
                subfield_command = multi_edit_engine.DeleteSubfieldCommand(subfield_code)
            elif action == self._subfield_action_types.replace_content:
                subfield_command = multi_edit_engine.ReplaceSubfieldContentCommand(subfield_code, value)
            elif action == self._subfield_action_types.replace_text:
                subfield_command = multi_edit_engine.ReplaceTextInSubfieldCommand(subfield_code, value, new_value)
            else:
                subfield_command = multi_edit_engine.BaseFieldCommand(subfield_code, value, new_value)

            commands_list.append(subfield_command)

        return commands_list


    def _create_commands_list(self, commands_json_structure):
        """Creates a list of commands recognized by multiedit engine"""

        commands_list = []

        for current_field in commands_json_structure:

            tag = current_field["tag"]
            ind1 = current_field["ind1"]
            ind2 = current_field["ind2"]
            action = current_field["action"]

            subfields = current_field["subfields"]
            subfield_commands = self._create_subfield_commands_list(subfields)

            # create appropriate command depending on the type
            if action == self._field_action_types.add:
                command = multi_edit_engine.AddFieldCommand(tag, ind1, ind2, subfield_commands)
            elif action == self._field_action_types.delete:
                command = multi_edit_engine.UpdateFieldCommand(tag, ind1, ind2, subfield_commands)
            elif action == self._field_action_types.update:
                command = multi_edit_engine.UpdateFieldCommand(tag, ind1, ind2, subfield_commands)
            else:
                # if someone send wrong action type, we use empty command
                command = multi_edit_engine.BaseFieldCommand()

            commands_list.append(command)

        return commands_list

def run_command(pattern, tag, value = None, delete = False, apply = False, 
                language=CFG_SITE_LANG):
    """Perform command on records matching pattern

    @param pattern: search text that will retrieve the records we want
    @param tag: the field whose value we wish to change
    @param value: the new value for @tag.  either a tuple of (old, new) 
                  strings or a single string
    @param delete: whether or not the record is to be deleted.  mutually 
                   exclusive with value
    @param apply: whether or not to apply these changes to the database
    @param language: preferred language of output text and boilerplate
    @return the modified text, and success indicator
    """
    # FIXME HACK XXX JRBL: START HERE, FINISH THIS BIT
    raise Exception, "Not Implemented"

def search(pattern, language=CFG_SITE_LANG):
    """Perform search and return however many MARC records as there are.
    
    @param pattern: pattern to search the record store for
    @param language: preferred language of output text and boilerplate
    @return a stream of MARC records
    """
    # FIXME: "hm" gets us back HTML-formatted MARC records; what we really
    #        want is plain-text MARC records - but that requires touching bibformat (?)
    return multi_edit_engine.perform_request_test_search(pattern, [],
                                                         "hm", None, language)

def check_command_line(opts, args):
    """Sanity-check the command line options; return error codes for problems.

    Exit Codes:
    0 : Success!  Everything looks OK
    1 : no search pattern specified
    2 : more than one command specified
    3 : command specified, but no tag 

    @param opts: option object returned by optparse.OptionParser().parse_args()
    @param args: argument list returned by optparse.OptionParser().parse_args()
    @return integer exit code"""
    if len(args) != 1: return 1
    commands = 0
    for o in (options.replace_pair, options.update_value, options.delete):
        if o: 
            commands += 1
            if (options.tag == None): return 3
    if commands > 1: return 2
    return 0

if __name__ == "__main__":
    
    # JRBL: Target Behavior:
    # bibedit --multiedit --search-pattern author:Ellis \
    #         --substitute-tag 710__a --substitution-mode substring \
    #         --change-value-from Fuu --change-value-to Foo\

    ln = CFG_SITE_LANG
    if 'LANG' in os.environ:
        ln = os.environ['LANG']
    ln = invenio.messages.wash_language(ln)
    _ = invenio.messages.gettext_set_language(ln)

    # FIXME: CLI should be fully internationalized; the options themselves 
    #        should remain stable, but the usage, description, and help text
    #        of each option should be updated for each supported language
    #        Cf. invenio.messages and ABOUT-NLS.
    #
    #        XXX: This can be done by bringing in a dictionary of values and
    #             then relying on it in deference to the text strings in
    #             usage, description, each of the "metavar" tags and each of 
    #             the "help" tags in each add_option() call below.
    cli_usage = "%prog [options] [PATTERN]" 
    cli_desc = "Updates records in one fell swoop.  Searches based on PATTERN.  Default behavior is to to preview changes only; use -A to make them permanent."
    parser = optparse.OptionParser(usage=cli_usage, description=cli_desc)
    parser.add_option('-t', '--substitute-tag', action="store", type="string",
                      dest="tag", nargs=1, default=None, 
                      metavar="[MARC tag]", 
                      help="Record tag to add, update or delete.  Mandatory with --update --replace and --delete.")
    parser.add_option('-r', '--replace', action="store", type="string",
                      dest="replace_pair", nargs=2, default=None, 
                      metavar="[old text] [new text]", 
                      help="Replace [old tex] with [new text].  Mutually exclusive with --update and --delete.")
    parser.add_option('-u', '--update', action="store", type="string",
                      dest="update_value", nargs=1, default=None, 
                      metavar="[new text]", 
                      help="Update record field to [new text].  Mutually exclusive with --replace and --delete.")
    parser.add_option('', '--DELETE', action="store_true", default=False,
                      dest="delete", 
                      help="DELETEs record; mutually exclusive with --update and --replace.")
    parser.add_option('-A', '--APPLY', action="store_true", default=False,
                      dest="apply", 
                      help="Make these changes permanent.")
    # FIXME: implement option for short output (record id, title, first 10 authors or whatever
    #        our search parameter matched, if we can figure that out
    options, args = parser.parse_args()

    exit_value = check_command_line(options, args)
    if exit_value != 0:
        parser.print_help()
    elif options.replace_pair != None:
        # do stuff: check apply, preview or replace
        print "replacing", options.replace_pair[0], "with", options.replace_pair[1] # FIXME
    elif options.update_value != None:
        # do stuff: check apply, preview or update
        print "updating with", options.update_value # FIXME
    elif options.delete:
        # do stuff: check apply, preview or delete
        print "deleting", options.tag # FIXME
    else:                                        # perform a simple search only
        print search(args[0], ln)

    # Be a good UNIX citizen and return our status to the shell
    sys.exit(exit_value)
