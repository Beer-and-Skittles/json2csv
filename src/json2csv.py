import os
import csv
import json

lib_info_keys = ['nom_voltage', 'nom_temperature', 'nom_process']
timing_info_keys = ['related_pin', 'timing_type', 'timing_sense']

class json2csv():

    def __init__(self, cell, input_path, output_path, display):

        if input_path != '' and os.path.exists(input_path) == False:
            raise AssertionError(f'Error: input path {input_path} does not exist')
        if output_path != '' and os.path.exists(output_path) == False:
            raise AssertionError(f'Error: output path {output_path} does not exist')
        
        self.display = display
        self.input_path = input_path
        self.output_path = output_path

        if cell == 'ALL':
            all_cells = self.search_cells(input_path)
            for each_cell in all_cells:
                self.json2csv(each_cell)
        else:
            self.json2csv(cell)
    
    def json2csv(self, cell):
        if self.display:
            print('working on',cell,'...')

        self.header = []
        self.csv_rows = []
        self.cell = cell
        self.header_completed = False
        self.read_json(self.input_path)
        self.write_csv(self.output_path)
        
    def search_cells(self, filepath):
        filename = next(os.walk(filepath), (None, None, []))[2][0]
        with open(filepath+filename) as libfile:
            data = json.load(libfile)
        name = [*data['library'].keys()][0]
        cells = data['library'][name]['cell'].keys()
        return[*cells]

    # read json file into csv_rows
    def read_json(self, filepath):

        filenames = next(os.walk(filepath), (None, None, []))[2]
        for filename in filenames:
            with open(filepath+filename) as libfile:
                data = json.load(libfile)

            name = [*data['library'].keys()][0]
            content = data['library'][name]['cell']
                

            cell_content = data['library'][name]['cell'][self.cell]
            if 'pin' not in cell_content.keys():
                return []

            pins = [*cell_content['pin'].keys()]

            lib_info = []
            for key in lib_info_keys:
                lib_info.append(data['library'][name][key])
            

            # pins
            for pin in pins:
                pin_content = cell_content['pin'][pin]
            
                if 'timing' in [*pin_content.keys()]:
                    
                    # to adapt both listed and single-entried timings
                    if type(pin_content['timing']) == type([]):
                        timing_contents = pin_content['timing']
                    else:
                        timing_contents = [pin_content['timing']]
                    
                    # complete header if had not
                    if not self.header_completed: 
                        self.header += lib_info_keys

                        timing_header = [[] for i in range(len(timing_info_keys))]
                        arch_types = []
                        for timing_content in timing_contents[int(len(timing_contents)/2):]:
                            for key, value in timing_content.items():
                                if key in timing_info_keys:
                                    header_name = key+' '+value
                                    header_idx  = timing_info_keys.index(key)
                                    if header_name not in timing_header[header_idx]:
                                        timing_header[header_idx].append(header_name)
                                else:
                                    if key not in arch_types:
                                        arch_types.append(key)
                        for th in timing_header:
                            self.header += th
                            
                        self.header += arch_types 
                        self.header += ['output_load', 'input_slope', 'value']
                        self.header_completed = True

                    # timing
                    for timing_content in timing_contents[int(len(timing_contents)/2):]:
                        pin_csv_row = lib_info + [0 for i in range(len(self.header) - len(lib_info))]
                        for key, value in timing_content.items():
                            
                            if key in timing_info_keys:
                                pin_csv_row[self.header.index(key+' '+value)] = 1

                            elif type(value) == type({}):
                                csv_row = self.parse_timing_arch(pin_csv_row, self.header.index(key), value)
                                if csv_row == []:
                                    return []
                                self.csv_rows += csv_row
                    break 
    
    # write collected information stored in csv_rows into csv file
    def write_csv(self, filepath):
        # self.csv_rows is empty : ANTENNA_RVT, BUSKP_RVT
        # 'pin' key DNE: DCAP_RVT, ...
        if self.csv_rows != []:
            csvfile = open(filepath + self.cell+'.csv', 'w', newline='')
            writer = csv.writer(csvfile)
            writer.writerow(self.header)
            for row in self.csv_rows:
                writer.writerow(row)
            csvfile.close()
            if self.display:
                print('success')
                print()
        elif self.display:
            print('FAIL')
            print()

    # parse timing arch
    def parse_timing_arch(self, list, arch_type, value):

        content = value[[*value.keys()][0]]
        if 'index_1' not in content.keys() or 'index_2' not in content.keys() or 'values' not in content.keys():
            return []

        output_loads = content['index_1'].split(', ')
        input_slopes = content['index_2'].split(', ')
        values = content['values'].split(', ')
        
        return_list = []
        for i in range(len(output_loads)):
            for j in range(len(input_slopes)):
                val_list = list.copy()
                val_list[arch_type] = 1
                val_list[-1] = values[i*7+j]
                val_list[-2] = input_slopes[i]
                val_list[-3] = output_loads[j]
                return_list.append(val_list)
        return return_list
