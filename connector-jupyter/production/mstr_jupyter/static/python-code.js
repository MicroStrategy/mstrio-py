/*jshint esversion: 6*/

var html_import = 
`from IPython.display import HTML\n`;

var hiding_code =
`HTML('''<script>\n` +
`$('div.input').hide();\n` +
`$('div.output').hide();\n` +
`</script>\n` +
`''')\n`;

function python_code_for_credentials(user, password) {
    var code = 
    `mstr_username = '${user}'\n` +
    `mstr_password = '${password}'`;

    return code;
}

function python_code_for_import(env, name, ds_type, ds_id, project_id, body, login_mode) {
    var py_body = ``+
      `attributes = ${(body.attributes.length > 0 ? JSON.stringify(body.attributes) : 'None')}, `+
      `metrics = ${(body.metrics.length > 0 ? JSON.stringify(body.metrics) : 'None')}, `+
      `attr_elements = ${(body.filters.length > 0 ? JSON.stringify(body.filters) : 'None')}`;

    var code =
    `# code importing ${name} from MicroStrategy\n\n` +
    `from mstrio.microstrategy import Connection \n` +
    `from mstrio.cube import Cube\n` +
    `from mstrio.report import Report \n\n` +
    `base_url = '${env}api'\n` +
    `login_mode = ${login_mode}\n` +
    `project_id = '${project_id}'\n\n` + 
    `conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, login_mode=login_mode)\n` + 
    `conn.connect()\n\n` +
    `${name} = ${ds_type.charAt(0).toUpperCase() + ds_type.slice(1)}(conn, '${ds_id}')\n` +
    `${name}.apply_filters(${py_body})\n` + 
    `${name}.to_dataframe()\n` + 
    `${name}_df = ${name}.dataframe\n` +
    `${name}_df`;

    return code;
}

function python_code_for_import_with_credentials_input(env, name, ds_type, ds_id, project_id, body, login_mode) {
  var py_body = ``+
    `attributes = ${(body.attributes.length > 0 ? JSON.stringify(body.attributes) : 'None')}, `+
    `metrics = ${(body.metrics.length > 0 ? JSON.stringify(body.metrics) : 'None')}, `+
    `attr_elements = ${(body.filters.length > 0 ? JSON.stringify(body.filters) : 'None')}`;

  var code =
  `# code importing ${name} from MicroStrategy\n\n` +
  `from mstrio.microstrategy import Connection \n` +
  `from mstrio.cube import Cube\n` +
  `from mstrio.report import Report \n` +
  `import getpass\n\n` +
  `mstr_username = input('username: ')\n` +
  `mstr_password = getpass.getpass('password: ')\n` +
  `base_url = '${env}api'\n` +
  `login_mode = ${login_mode}\n` +
  `project_id = '${project_id}'\n\n` + 
  `conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, login_mode=login_mode)\n` + 
  `conn.connect()\n\n` +
  `${name} = ${ds_type.charAt(0).toUpperCase() + ds_type.slice(1)}(conn, '${ds_id}')\n` +
  `${name}.apply_filters(${py_body})\n` + 
  `${name}.to_dataframe()\n` +
  `${name}_df = ${name}.dataframe\n\n` +
  `${name}_df`;
  
  return code;
}

function python_code_for_export(dataframes, wrangled, save_as_name, folder_id, env, project_id, login_mode) { 
    var string_add_tables = "";
    var to_m, to_a;
    dataframes.forEach((dataframe) => {
      to_m = []
      to_a = []
      if (wrangled[dataframe]) {
        if (wrangled[dataframe].toMetrics && wrangled[dataframe].toMetrics[0]) {wrangled[dataframe].toMetrics.forEach(el => {to_m.push('"'+el+'"')}); to_m = '['+to_m+']'} else {to_m = "None"}
        if (wrangled[dataframe].toAttributes && wrangled[dataframe].toAttributes[0]) {wrangled[dataframe].toAttributes.forEach(el => {to_a.push('"'+el+'"')}); to_a = '['+to_a+']'} else {to_a = "None"}
      } else {
        to_m = "None"
        to_a = "None"
      }
      string_add_tables += `dataset.add_table(name="${dataframe}", data_frame=${dataframe}, update_policy="add", to_metric=${to_m}, to_attribute=${to_a})\n`;
    });

    var code =
    `# code exporting ${dataframes} to MicroStrategy\n\n` +
    `from mstrio.microstrategy import Connection \n` +
    `from mstrio.dataset import Dataset\n` +
    `base_url = '${env}api'\n` +
    `login_mode = ${login_mode}\n` +
    `project_id = '${project_id}'\n\n` + 
    `conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, login_mode=login_mode)\n` + 
    `conn.connect()\n\n` +
    `dataset = Dataset(conn, name="${save_as_name}")\n` +
    `${string_add_tables}\n` +
    `dataset.create(folder_id="${folder_id}")\n`;

    return code;
}

function python_code_for_export_with_credentials_input(dataframes, wrangled, save_as_name, folder_id, env, project_id, login_mode) { 
  var string_add_tables = "";
  var to_m, to_a;
  dataframes.forEach((dataframe) => {
    to_m = []
    to_a = []
    if (wrangled[dataframe]) {
      if (wrangled[dataframe].toMetrics && wrangled[dataframe].toMetrics[0]) {wrangled[dataframe].toMetrics.forEach(el => {to_m.push('"'+el+'"')}); to_m = '['+to_m+']'} else {to_m = "None"}
      if (wrangled[dataframe].toAttributes && wrangled[dataframe].toAttributes[0]) {wrangled[dataframe].toAttributes.forEach(el => {to_a.push('"'+el+'"')}); to_a = '['+to_a+']'} else {to_a = "None"}
    } else {
      to_m = "None"
      to_a = "None"
    }
    string_add_tables += `dataset.add_table(name="${dataframe}", data_frame=${dataframe}, update_policy="add", to_metric=${to_m}, to_attribute=${to_a})\n`;
  });

  var code =
  `# code exporting ${dataframes} to MicroStrategy\n\n` +
  `from mstrio.microstrategy import Connection \n` +
  `from mstrio.dataset import Dataset\n` +
  `import getpass\n\n` +
  `mstr_username = input('username: ')\n` +
  `mstr_password = getpass.getpass('password: ')\n` +
  `base_url = '${env}api'\n` +
  `login_mode = ${login_mode}\n` +
  `project_id = '${project_id}'\n\n` + 
  `conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, login_mode=login_mode)\n` + 
  `conn.connect()\n\n` +
  `dataset = Dataset(conn, name="${save_as_name}")\n` +
  `${string_add_tables}\n` +
  `dataset.create(folder_id="${folder_id}")\n`;

  return code;
}

function python_code_for_listing_dataframe_names() {
  var code = 
  `import pandas as pd\n` +
  `dataframe_names=[]\n` +    
  `for el in dir():\n` +
  `    if isinstance(locals()[el], pd.core.frame.DataFrame)  and el[0]!='_':\n` +
  `        dataframe_names.append(el)\n` +
  `import_string = ""\n` +
  `for df___el in dataframe_names:\n` + 
  `    import_string += '{"name":"' + df___el + '","rows":' + str(eval(df___el + '.shape[0]')) + ',"columns":' + str(eval(df___el + '.shape[1]')) + '},'\n` +
  `import_string = "[" + import_string[0:len(import_string) - 1] + "]"\n` + 
  `import_string`;

  return code;
}

function python_code_for_info() {
  var code = 
  `i1 = !jupyter --version\n` + 
  `i2 = !python --version\n` +
  `i3 = !where python\n` +
  `info = '{"Jupyter Version":"' + str(i1).replace(" ", "").replace(",", " - ").replace("\\\\", "").replace("'", "") + '","Python Version":"' + str(i2).replace("\\\\", "").replace("'", "") + '","Python path":"' + str(i3).replace("\\\\", "/").replace("'", "") + '"}'\n` +
  `info\n`;

  return code;
}

function python_code_for_column_reorder(df_name, cols_names, index) {
  var code =
  `var = ${df_name}.columns.tolist()\n` +
  `index = ${index}\n` +
  `cols = ${cols_names}\n` +
  `new = [el for el in var if not el in cols]\n` +
  `new = new[:index] + cols + new[index:]\n` +
  `${df_name} = ${df_name}[new]\n`

  return code
}

function python_code_for_cube_details(env, cube_id, project_id, login) {
  var code =
  `from mstrio.microstrategy import Connection \n` +
  `from mstrio.cube import Cube\n` +
  `from mstrio.report import Report \n\n` +
  `mstr_username = '${login.username}'\n` +
  `mstr_password = '${login.password}'\n` +
  `base_url = '${env}api'\n` +
  `login_mode = ${login.loginMode}\n` +
  `project_id = '${project_id}'\n\n` + 
  `conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, login_mode=login_mode)\n` + 
  `conn.connect()\n\n` +
  `temp_cube = Cube(conn, '${cube_id}')\n` +
  `temp_md = temp_cube.multitable_definition()\n` +
  `temp_attr = temp_cube.attributes\n` +
  `temp_metr = temp_cube.metrics\n` +
  `{"definition": temp_md, "attributes": temp_attr, "metrics": temp_metr}`;

  return code;
}
