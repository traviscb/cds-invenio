## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

#__revision__ = "$Id$"

   ## Description:   function Print_Success_CPLX
   ##                This function outputs a message telling the user his/her
   ##             request was taken into account.
   ## Author:         A.Voitier
   ## PARAMETERS:    -

import os

from invenio.websubmit_config import InvenioWebSubmitFunctionError

def Print_Success_CPLX(parameters,curdir,form):
    global rn
    act = form['act']
    t="<br><br><B>Your request has been taken into account!</B><br><BR>"
    if (act == "RRP") or (act == "RPB"):
        t+="An email has been sent to the Publication Committee Chair. You will be warned by email as soon as the Project Leader takes his/her decision regarding your document.<br><br>"
    elif act == "RDA":
        t+="An email has been sent to the Project Leader. You will be warned by email as soon as the Project Leader takes his/her decision regarding your document.<br><br>"
    return t
