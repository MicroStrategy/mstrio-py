/*jshint esversion: 6*/
var html_import =
`from IPython.display import HTML\n`;

var hiding_code =
`HTML('''<script>
$('div.input').hide();
$('div.output').hide();
</script>
''')`;

function python_code_for_credentials(user, password) {
  var code =
`mstr_username = '${user || ''}'
mstr_password = '${password || ''}'`;

  return code;
}

function python_code_for_import(env, name, ds_type, ds_id, project_id, body, login_mode) {
  var py_body;
  if (body.attributes.length + body.metrics.length + body.filters.length === 0) {
    py_body = 'attributes = None, metrics = None, attr_elements = None'
  } else {
    py_body = `` +
      `attributes = ${JSON.stringify(body.attributes)}, ` +
      `metrics = ${JSON.stringify(body.metrics)}, ` +
      `attr_elements = ${body.filters.length > 0 ? JSON.stringify(body.filters) : 'None'}`;
  }

  var code =
`# code importing ${name} from MicroStrategy

from mstrio.microstrategy import Connection
from mstrio.cube import Cube
from mstrio.report import Report

base_url = '${env}'
login_mode = ${login_mode}
project_id = '${project_id}'

conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, login_mode=login_mode)
conn.connect()

${name} = ${ds_type.charAt(0).toUpperCase() + ds_type.slice(1)}(conn, '${ds_id}')
${name}.apply_filters(${py_body})
${name}.to_dataframe()
${name}_df = ${name}.dataframe

${name}_df`;

  return code;
}

function python_code_for_import_with_credentials_input(env, name, ds_type, ds_id, project_id, body, login_mode) {
  var py_body;
  if (body.attributes.length + body.metrics.length + body.filters.length === 0) {
    py_body = 'attributes = None, metrics = None, attr_elements = None'
  } else {
    py_body = `` +
      `attributes = ${JSON.stringify(body.attributes)}, ` +
      `metrics = ${JSON.stringify(body.metrics)}, ` +
      `attr_elements = ${body.filters.length > 0 ? JSON.stringify(body.filters) : 'None'}`;
  }

  var code =
`# code importing ${name} from MicroStrategy

from mstrio.microstrategy import Connection
from mstrio.cube import Cube
from mstrio.report import Report
import getpass

mstr_username = input('username: ')
mstr_password = getpass.getpass('password: ')
base_url = '${env}'
login_mode = ${login_mode}
project_id = '${project_id}'

conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, login_mode=login_mode)
conn.connect()

${name} = ${ds_type.charAt(0).toUpperCase() + ds_type.slice(1)}(conn, '${ds_id}')
${name}.apply_filters(${py_body})
${name}.to_dataframe()
${name}_df = ${name}.dataframe

${name}_df`;

  return code;
}

function python_code_for_export(custom_env, dataframes, save_as_name, folder_id, certify, description, env, project_id, login_mode) {
  var tablesCode = dataframes.map(({ name, attributes, metrics }) => (
    `dataset.add_table(name="${name}", data_frame=${custom_env}['${name}'], update_policy="add", `+
    `to_metric=${metrics.length ? JSON.stringify(metrics) : 'None'}, `+
    `to_attribute=${attributes.length ? JSON.stringify(attributes) : 'None'})`
  ));

  var code =
`# code exporting ${save_as_name} to MicroStrategy

from mstrio.microstrategy import Connection
from mstrio.dataset import Dataset

base_url = '${env}'
login_mode = ${login_mode}
project_id = '${project_id}'

conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, login_mode=login_mode)
conn.connect()

dataset = Dataset(conn, name="${save_as_name}"${description ? `, description="${description}"` : ''})
${tablesCode.join('\n')}
dataset.create(folder_id="${folder_id}")
${certify ? 'dataset.certify()' : ''}`;

  return code.trim();
}

function python_code_for_export_with_credentials_input(custom_env, dataframes, save_as_name, folder_id, certify, description, env, project_id, login_mode) {
  var tablesCode = dataframes.map(({ name, attributes, metrics }) => (
    `dataset.add_table(name="${name}", data_frame=${custom_env}['${name}'], update_policy="add", `+
    `to_metric=${metrics.length ? JSON.stringify(metrics) : 'None'}, `+
    `to_attribute=${attributes.length ? JSON.stringify(attributes) : 'None'})`
  ));

  var code =
`# code exporting ${save_as_name} to MicroStrategy

### This code does not apply any Data Modeling Steps ###
### If it should, please use the connector addon to prepare data ###

from mstrio.microstrategy import Connection
from mstrio.dataset import Dataset
import getpass

mstr_username = input('username: ')
mstr_password = getpass.getpass('password: ')
base_url = '${env}'
login_mode = ${login_mode}
project_id = '${project_id}'

conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, login_mode=login_mode)
conn.connect()

dataset = Dataset(conn, name="${save_as_name}"${description ? `, description="${description}"` : ''})
${tablesCode.join('\n')}
dataset.create(folder_id="${folder_id}")
${certify ? 'dataset.certify()' : ''}`;

  return code.trim();
}

function python_code_for_update(custom_env, env, login_mode, project_id, dataset_id, policies) {
  var string_add_tables = "";
  var tables = [];
  policies.forEach(({ tableName, updatePolicy }) => {
    tables.push(tableName);
    string_add_tables += `dataset.add_table(name="${tableName}", data_frame=${custom_env}['${tableName}'], update_policy="${updatePolicy}")\n`;
  });

  var code =
`# code updating ${tables.join(', ')} table(s) to MicroStrategy

from mstrio.microstrategy import Connection
from mstrio.dataset import Dataset

base_url = '${env}'
login_mode = ${login_mode}
project_id = '${project_id}'

conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, login_mode=login_mode)
conn.connect()

dataset = Dataset(conn, dataset_id="${dataset_id}")
${string_add_tables}
dataset.update()
dataset.publish()`;

  return code;
}

function python_code_for_update_with_credentials_input(custom_env, env, login_mode, project_id, dataset_id, policies) {
  var string_add_tables = "";
  var tables = [];
  policies.forEach(({ tableName, updatePolicy }) => {
    tables.push(tableName);
    string_add_tables += `dataset.add_table(name="${tableName}", data_frame=${custom_env}['${tableName}'], update_policy="${updatePolicy}")\n`;
  });

  var code =
`# code updating ${tables.join(', ')} table(s) to MicroStrategy

### This code assumes dataframes' structure is consistent with cube structure ###
### If it's not, please use the connector addon to prepare data ###

from mstrio.microstrategy import Connection
from mstrio.dataset import Dataset
import getpass

mstr_username = input('username: ')
mstr_password = getpass.getpass('password: ')
base_url = '${env}'
login_mode = ${login_mode}
project_id = '${project_id}'

conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, login_mode=login_mode)
conn.connect()

dataset = Dataset(conn, dataset_id="${dataset_id}")
${string_add_tables}
dataset.update()
dataset.publish()`;

  return code;
}

function python_code_for_listing_dataframe_names() {
  var code =
`import pandas as pd

dataframe_names=[]
for el in dir():
    if isinstance(locals()[el], pd.core.frame.DataFrame) and el[0]!='_':
        dataframe_names.append(el)

import_string = ""
for df___el in dataframe_names:
    import_string += '{"name":"' + df___el + '","rows":' + str(eval(df___el + '.shape[0]')) + ',"columns":' + str(eval(df___el + '.shape[1]')) + '},'

import_string = "[" + import_string[0:len(import_string) - 1] + "]"
import_string`;

  return code;
}

function python_code_for_info() {
  var code =
`i1 = !jupyter --version
i2 = !python --version
i3 = !where python
info = '{"Jupyter Version":"' + str(i1).replace(" ", "").replace(",", " - ").replace("\\\\", "").replace("'", "") + '","Python Version":"' + str(i2).replace("\\\\", "").replace("'", "") + '","Python path":"' + str(i3).replace("\\\\", "/").replace("'", "") + '"}'
info`;

  return code;
}

function python_code_for_column_reorder(df_name, cols_names, index) {
  var code =
`var = ${df_name}.columns.tolist()
index = ${index}
cols = ${cols_names}
new = [el for el in var if not el in cols]
new = new[:index] + cols + new[index:]
${df_name} = ${df_name}[new]`;

  return code
}

function python_code_for_gathering_dataframe_data(dataframe_name) {
  var code =
`${dataframe_name}[:10].to_json(orient='records')`;

  return code;
}

function python_code_for_modeling_gathered_data(dataframe_name) {
  var code =
`from mstrio.utils.model import Model

arg_for_model = [{'table_name': 'selected_df', 'data_frame': ${dataframe_name}[:10]}]
model = Model(tables=arg_for_model, name='preview_table_types', ignore_special_chars=True)

model.get_model()`;

  return code;
}

function python_code_for_dataframe_columns_selection(custom_env, selected_objects, dataframe_name) {
  var code =
`cols_to_leave = ${JSON.stringify(selected_objects)}
final_cols = [name for name in ${custom_env}['${dataframe_name}'].columns if name not in cols_to_leave]
${custom_env}['${dataframe_name}'] = ${custom_env}['${dataframe_name}'].drop(columns=final_cols)`;

  return code;
}

function python_code_for_cube_details(env, cube_id, project_id, login) {
  var code =
`from mstrio.microstrategy import Connection
from mstrio.cube import Cube
from mstrio.report import Report

mstr_username = '${login.username}'
mstr_password = '${login.password}'
base_url = '${env}'
login_mode = ${login.loginMode}
project_id = '${project_id}'

conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id, login_mode=login_mode)
conn.connect()

temp_cube = Cube(conn, '${cube_id}')
temp_md = temp_cube.multitable_definition()
temp_attr = temp_cube.attributes
temp_metr = temp_cube.metrics

{"definition": temp_md, "attributes": temp_attr, "metrics": temp_metr}`;

  return code;
}
