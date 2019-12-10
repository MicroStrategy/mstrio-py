// /*jshint esversion: 6*/

function create_import_cell(env, ds_name, ds_id, dataset_type, project_id, body, login_mode, user, password) {
  var name = ds_name.split(' ').join('_').replace(/[^A-Za-z0-9_]/gi, '');

  if(/\d/.test(name[0])) {
    name = "var_" + name;
  }

  execute_credentials_kernel_background(user, password);

  Jupyter.notebook
    .insert_cell_at_index("code", 0)
    .set_text(python_code_for_import(env, name, dataset_type, ds_id, project_id, body, login_mode));
  Jupyter.notebook.get_cell(0).execute();
  Jupyter.notebook.get_cell(0).set_text(python_code_for_import_with_credentials_input(env, name, dataset_type, ds_id, project_id, body, login_mode));
}

function create_export_cell(dataframes, wrangled, save_as_name, folder_id, env, project_id, login_mode, user, password) {
    execute_credentials_kernel_background(user, password);
    
    Jupyter.notebook
      .insert_cell_at_index("code", 10000)
      .set_text(python_code_for_export(dataframes, wrangled, save_as_name, folder_id, env, project_id, login_mode));
    Jupyter.notebook.get_cell(-1).execute();
    Jupyter.notebook.get_cell(-1).set_text(python_code_for_export_with_credentials_input(dataframes, wrangled, save_as_name, folder_id, env, project_id, login_mode));
}
