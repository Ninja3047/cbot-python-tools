import gspread

# Connect to Google spreadsheet for logging

class gspread_log():

	def __init__(self, uname, pword, sheet_name):

		gc = gspread.login(uname,pword)

		self.wks = gc.open(sheet_name).sheet1
		
		#determine current log lengths
		self.n = len(self.wks.col_values(3)) + 1
		self.rt_n = len(self.wks.col_values(1)) + 1
		self.last_msg = "" #keeps track of last message
		
	def write(self, pstring):
		"""
		writes a message to real-time and past log 
		"""
		if "[Stranger" in pstring and "[Stranger" in self.last_msg:
			return #dont log repeated connection attempts
		else:
			self.wks.update_cell(self.rt_n, 1, pstring)
			self.rt_n += 1
			
			self.wks.update_cell(self.n, 3, pstring)
			self.n += 1	
			self.last_msg = pstring

	def clear_rt(self):
		"""
		clear the realtime log
		"""
		if self.n > 2:
			self.wks.update_cell(self.n, 3, "")
			self.n += 1	
		
		cell_list = self.wks.range('A2:A'+str(self.rt_n))

		for cell in cell_list:
			cell.value = ''
		self.wks.update_cells(cell_list)	
		self.rt_n = 2
		
	def clear_perm(self):
		"""
		clear the past log
		"""
		cell_list = self.wks.range('C2:C'+str(self.n))

		for cell in cell_list:
			cell.value = ''
		self.wks.update_cells(cell_list)	
		self.n = 2	

if __name__ == "__main__":
	# a sample test
	uname = "noone@gmail.com" #google docs username
	pword = "1234" #google docs password
	sheet_name = "cleverbot log" #create google spreadsheet with this name
	g = gspread_log()
	g.clear_rt()
	g.clear_perm()
	g.write("oh hi")
	g.write("how are you")
	g.clear_rt()
	g.write("oh hi2")
	g.write("how are you2")
	g.clear_rt()
	g.clear_perm()