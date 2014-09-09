# vim:sw=8:ts=8:et:nowrap
# -*- coding: latin-1 -*-

# extend-xml.py takes the current peers-ucl.xml and adds the missing forenames,
# of-names, counties, and surnames.

import sys
import os
sys.path.append('./')
sys.path.append('lords/')
os.chdir('../../pyscraper/')
import re
import xml.sax
import codecs

class LordsList(xml.sax.handler.ContentHandler):
	def __init__(self):
		self.lords={} # ID --> MPs
		self.lordnames={} # "lordnames" --> lords
		parser = xml.sax.make_parser()
		parser.setContentHandler(self)
		parser.parse("../members/peers-ucl.xml")

	# check that the lordofnames that are blank happen after the ones that have values
	# where the lordname matches
	def startElement(self, name, attr):
		""" This handler is invoked for each XML element (during loading)"""
		if name == "lord":
			if self.lords.get(attr["id"]):
				raise Exception, "Repeated identifier %s in members XML file" % attr["id"]

			# needs to make a copy into a map because entries can't be rewritten
                        xMP = 'ex_MP' in attr and attr["ex_MP"] or ''
			cattr = { "id":attr["id"],
					  "title":attr["title"], "lordname":attr["lordname"], "lordofname":attr["lordofname"],
					  "fromdate":attr["fromdate"], "todate":attr["todate"], "forenames":attr["forenames"],
                                          "peeragetype":attr["peeragetype"], "ex_MP":xMP, "party":attr["affiliation"] }
			self.lords[attr["id"]] = cattr

			lname = attr["lordname"] or attr["lordofname"]
			lname = re.sub("\.", "", lname)
			assert lname
			self.lordnames.setdefault(lname, []).append(cattr)

lordsList = LordsList()

fh = codecs.open('../members/beamish/BeamishParsed')
attrlist = None
forenames = {}
lordofname = {}
surname = {}
county = {}
for row in fh.readlines():
        s = row.strip().split(',')
	assert len(s) == 12
	if not attrlist:
		attrlist = s
		continue
	lordattr = {}
	for (a, b) in zip(attrlist, s):
		lordattr[a] = b

        lord = lordsList.lords.get(lordattr['ID'])

        if lordattr['Lordof Name'] == 'St. Marylebone':
                lordattr['Lordof Name'] = 'St Marylebone'

        # Deal with Hereditaries who got Life Peerages in the 1999 debacle
        if lordattr['Type'] == 'L:H':
                lordattr['Type'] = 'L'
        if lordattr['Lord Name'] == 'Aldington' or (lordattr['Lord Name'] == 'Erroll' and lordattr['Lordof Name']=='Hale'):
                lordattr['Type'] = 'L'

        # Beamish missing one death
        if lordattr['Lord Name'] == 'Erroll' and lordattr['Lordof Name']=='Hale':
                lordattr['Died'] = '2000-09-14'
        # And newspapers don't agree on this one
        if lordattr['Lord Name'] == 'Clark' and lordattr['Lordof Name']=='Kempston':
                lordattr['Died'] = '2004-10-06'

        # More Hereditaries -> Life Peerages stuff
        if lordattr['Lord Name'] == 'Aldington':
                lordattr['Created'] = '1962'
        if lordattr['Lord Name'] == 'Erroll' and lordattr['Lordof Name']=='Hale':
                lordattr['Created'] = '1964'
        if lordattr['Lord Name'] == 'Shepherd':
                lordattr['Created'] = '1954'
        if lordattr['Lord Name'] == 'Windlesham':
                lordattr['Created'] = '1962'
        if lordattr['Lord Name'] == 'Belstead':
                lordattr['Created'] = '1958'

        # DO NOT ASK HOW LONG THIS TOOK
        # But link up everything with current stuff and check
        assert(lordattr['Type'] == lord['peeragetype'])
        assert( (len(lord['fromdate'])==4 and lordattr['Created'][0:4]<=lord['fromdate']) or (len(lord['fromdate'])>4 and lordattr['Created']<=lord['fromdate']))
        assert(lordattr['Died'] == lord['todate'] or (not lordattr['Died'] and lord['todate']=='9999-12-31'))
        assert(lordattr['Rank'] == lord['title'])
        assert(lordattr['Lordof Name'] == lord['lordofname'])
        assert(lordattr['Lord Name'] == lord['lordname'])

        if not (lord['lordname'] == 'Park' and lord['title'] == 'Baroness') and lordattr['Forenames'] != lord['forenames']:
                forenames[lordattr['ID']] = lordattr['Forenames']
        if lordattr['Lord Place'] != lord['lordofname']:
                lordofname[lordattr['ID']] = lordattr['Lord Place']
        if lordattr['Surname'] != lord['lordname']:
                surname[lordattr['ID']] = lordattr['Surname']
        county[lordattr['ID']] = lordattr['County']
fh.close()

def sortDict(d):
        keys = d.keys()
        keys.sort()
        return map(d.get, keys)

fout = open("../members/beamish/peers-ucl2.xml", "w")
fout.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n')
fout.write('\n\n<!-- Generated by extend-xml.py, from the modified output of peers-ucl-conv.py from database dump of the house made on 2005-12-03 -->\n\n\n')
fout.write('<publicwhip>\n\n')
for row in sortDict(lordsList.lords):
	fout.write('<lord\n')
	fout.write('\tid="%s"\n' % row['id'])
	fout.write('\thouse="lords"\n')
	fout.write('\tforenames="%s"\n' % row['forenames'])
        if row['id'] in forenames:
                fout.write('\tforenames_full="%s"\n' % forenames[row['id']])
        if row['id'] in surname:
                fout.write('\tsurname="%s"\n' % surname[row['id']])
	fout.write('\ttitle="%s" lordname="%s" lordofname="%s"\n' % (row['title'], row['lordname'], row['lordofname']))
        if row['id'] in lordofname:
                fout.write('\tlordofname_full="%s"\n' % lordofname[row['id']])
        if row['id'] in county:
                fout.write('\tcounty="%s"\n' % county[row['id']])
	fout.write('\tpeeragetype="%s" affiliation="%s"\n' % (row['peeragetype'], row['party']))
	fout.write('\tfromdate="%s" todate="%s"\n' % (row['fromdate'], row['todate']))
	if row['ex_MP'] == 'yes':
		fout.write('\tex_MP="yes"\n')
	fout.write('/>\n')
fout.write("\n</publicwhip>\n")
fout.close()
