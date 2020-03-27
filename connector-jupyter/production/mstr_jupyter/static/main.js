/*jshint esversion: 6*/
define(["jquery", "base/js/namespace", "base/js/dialog"], function(
    $,
    Jupyter,
    dialog
) {
  "use strict";

  const snippet_for_loading = "?loading=true";
  const origin = window.location.origin;
  const connector_address = `${origin}/nbextensions/mstr_jupyter/mstr-connector/build/index.html`;
  const MSTR_ENV_VARIABLE_NAME = 'mstrio_env';

  const pythonCodeForInitialEngine = (envName) => {
    var code =
`import pandas as pd

def create_custom_env():
    output={}
    for el in globals().keys():
        if el[0]!='_' and isinstance(globals()[el], pd.core.frame.DataFrame):
            output[el] = globals()[el]
    return output

def update_custom_env():
    global ${envName}
    new_${envName} = ${envName}
    for el in globals().keys():
        if el[0]!='_' and isinstance(globals()[el], pd.core.frame.DataFrame) and not el in new_${envName}.keys():
            new_${envName}[el] = globals()[el]
    return new_${envName}


if '${envName}' in locals():
    ${envName} = update_custom_env()
else:
    ${envName} = create_custom_env()`;

    return code;
  }

  var modal;
  var mstr_editor;
  var current_mode;
  var selectedProjects;
  var credentials_login;
  var token_login;
  var importing_exporting_flag;

  var initialize = function() {
      Jupyter.toolbar.add_buttons_group([
          Jupyter.keyboard_manager.actions.register({
                  help: "Connect to MicroStrategy",
                  icon: " ",
                  handler: show_mstr_editor_modal
              },
              "connect-to-microstrategy",
              "mstr_it"
          )
      ]);

      $("[title='Connect to MicroStrategy']").append(
          `<img style="padding-bottom: 2px" src="${origin}/nbextensions/mstr_jupyter/mstr.ico">`
      ).bind('keydown', function(event) {
        if (event.key === ' ') {
          event.preventDefault();
          $(this).click();
        }
      });
  };

  // appending custom MSTRIO files
  appendHead("python-code.js");
  appendHead("cells-creation.js");
  appendHead("utilities.js");
  appendHead("override_style.css");

  Jupyter.notebook.kernel.execute(
    pythonCodeForInitialEngine(MSTR_ENV_VARIABLE_NAME),
  );

  function build_mstr_editor() {
    mstr_editor = $("<div id='mstr_editor'/>");

    window.onmessage = async function(event) {
      var mstr_envs_LocalStorage;
      var mstr_projs_LocalStorage;
      var e = event.data;
      var c = e.connectionData;
      var a = e.authenticationInfo;
      var x = e.exportInfo;

      Jupyter.notebook.kernel.execute(
        pythonCodeForInitialEngine(MSTR_ENV_VARIABLE_NAME),
      );

      window.backendManager = document.getElementById("mstr_iframe").contentWindow.backendManager;
      var backendManager = window.backendManager;

      switch(e.message_type) {
        case "import":
          modal.modal("hide");
          create_import_cell(c.url, c.name, c.datasetId, c.datasetType, c.projectId, c.body, a.loginMode, a.username, a.password);

          importing_exporting_flag = true;
          var interval_var = setInterval(checkImportExport, 2000, "importing", importing_exporting_flag);
          localStorage.setItem("interval_var", interval_var);
          break;

        case "conn_load":
          var iframe_document = document.getElementById("mstr_iframe").contentWindow.document;
          appendHead("iframe_style.css", iframe_document);
          mstr_envs_LocalStorage = localStorage.getItem("mstr_envs");
          mstr_projs_LocalStorage = localStorage.getItem("mstr_projs");

          if(mstr_envs_LocalStorage) backendManager.addEnvToSuggestions(mstr_envs_LocalStorage);
          if(mstr_projs_LocalStorage) backendManager.addRecentProjects(mstr_projs_LocalStorage);

          if(importing_exporting_flag === true && (isImportingExporting("importing", importing_exporting_flag) || isImportingExporting("exporting", importing_exporting_flag))) {backendManager.toggleImportOrExportInProgress(true);}
          else {backendManager.toggleImportOrExportInProgress(false);}

          let envName;
          let selectedProjectsList;

          if(credentials_login) {
            envName = credentials_login.envName;
          }

          if(selectedProjects) {
            selectedProjectsList = JSON.parse(selectedProjects).filter(e => e.envName === envName)[0].projectList;
          }

          if(current_mode !== 'authentication' && selectedProjects && credentials_login && token_login) {
            backendManager.automaticLogin(credentials_login, token_login, current_mode, selectedProjectsList);
          }
          else {
            backendManager.showAuthenticationPage();
          }

          executePythonInBackground(Jupyter.notebook, python_code_for_listing_dataframe_names())
            .then((out) => {
              if (out.msg_type === "execute_result") {
                var dataframe_names = out.content.data["text/plain"];
                backendManager.updateDataFramesList(dataframe_names.slice(1, dataframe_names.length - 1));
              } else {
                // something else has been done in background or ERROR!
              }
            })
          break;

        case "update_envs":
          var newEnvInfos_stringified = e.value;
          backendManager.addEnvToSuggestions(newEnvInfos_stringified);
          localStorage.setItem("mstr_envs", newEnvInfos_stringified);
          break;

        case "update_proj":
          var newRecentProjects_stringified = e.value;
          selectedProjects = e.value;

          backendManager.addRecentProjects(newRecentProjects_stringified);
          localStorage.setItem("mstr_projs", newRecentProjects_stringified);
          break;

        case "clear_all_env":
          localStorage.removeItem("mstr_envs");
          break;

        case "update_mode":
          var modal_dialog = document.getElementsByClassName("modal-dialog");
          changeSize(e.value, modal_dialog[0]);

          current_mode = e.value;

          if (current_mode === 'authentication') {
            var iframe_document = document.getElementById("mstr_iframe").contentWindow.document;
            var h1 = iframe_document.querySelector('h1');
            h1.focus()
          }
          break;

        case "export_mode":
          var notebook_name = document.getElementById("notebook_name").innerText;
          backendManager.setBackendEnvName(notebook_name);

          executePythonInBackground(Jupyter.notebook, python_code_for_listing_dataframe_names())
            .then((out) => {
              if (out.msg_type === "execute_result") {
                var dataframe_names = out.content.data["text/plain"];
                backendManager.updateDataFramesList(dataframe_names.slice(1, dataframe_names.length - 1));
              } else {
                // something else has been done in background or ERROR!
              }
            })
          break;

        case "gather_df_details":
          var df_name = {
            original: e.dataframe_org_name,
            changed: e.dataframe_new_name ? e.dataframe_new_name : e.dataframe_org_name
          };
          var py_code = python_code_for_gathering_dataframe_data(df_name.original);
          executePythonInBackground(Jupyter.notebook, py_code)
            .then((out) => {
              if (out.msg_type === "execute_result") {
                var output = (
                  out.content.data["text/plain"]
                    .replace(/\\{2,}/gi, "\\")
                    .replace(/'/gi, '"')
                );
                var finalReturnObject = {
                  content: JSON.parse(output.slice(1, output.length-1)),
                  originalName: df_name.changed
                }
                py_code = python_code_for_modeling_gathered_data(df_name.original);
                executePythonInBackground(Jupyter.notebook, py_code)
                  .then((out) => {
                    if (out.msg_type === "execute_result") {
                      output = (
                        out.content.data["text/plain"]
                          .replace(/\\{2,}/gi, "\\")
                          .replace(/'/gi, '"')
                      );
                      var clearedStructure = JSON.parse(output)
                      clearedStructure.attributes = clearedStructure.attributes.map((item) => ({
                        ...item,
                        name: [item.name]
                      }))
                      clearedStructure.metrics = clearedStructure.metrics.map((item) => ({
                        ...item,
                        name: [item.name]
                      }))
                      clearedStructure.tables[0].columnHeaders = clearedStructure.tables[0].columnHeaders.map((item) => ({
                        ...item,
                        name: [item.name]
                      }))
                      finalReturnObject["types"] = clearedStructure
                      backendManager.updateDataFrameContent(finalReturnObject, df_name.changed);
                    } else {
                      // something else has been done in background or ERROR!
                    }
                  })
              } else {
                // something else has been done in background or ERROR!
              }
            })
          break;

        case "gather_cube_details":
          executePythonInBackground(Jupyter.notebook, python_code_for_cube_details(c.url, c.cubeId, c.projectId, a))
            .then((out) => {
              if (out.msg_type === "execute_result") {
                var result = JSON.parse(out.content.data["text/plain"].replace(/'/gi, '"'));
                backendManager.updateCubeDetails(c.name, result);
              } else {
                // something else has been done in background or ERROR!
              }
            })
          break;

        case "export_dataframe":
          modal.modal("hide");
          create_export_cell(MSTR_ENV_VARIABLE_NAME, x.selectedDataframes, x.saveAsName, x.folderId, x.certify, x.description, a.envUrl, x.projectId, a.loginMode, a.username, a.password);

          importing_exporting_flag = true;
          var interval_var = setInterval(checkImportExport, 2000, "exporting", importing_exporting_flag);
          localStorage.setItem("interval_var", interval_var);
          break;

        case "update_cube":
          modal.modal("hide");
          create_update_cell(MSTR_ENV_VARIABLE_NAME, a.envUrl, a.loginMode, x.projectId, x.cubeId, x.updatePolicies, a.username, a.password);

          importing_exporting_flag = true;
          var interval_var = setInterval(checkImportExport, 2000, "updating", importing_exporting_flag);
          localStorage.setItem("interval_var", interval_var);
          break;

        case "wrangle_col_reorder":
            var instructions = JSON.parse(e.instructionDetails)
            var formattedCols = ''
            instructions.cols.forEach((el) => {
              formattedCols += '"'+el+'", '
            })
            formattedCols = "["+ formattedCols.substring(0, formattedCols.length-2) +"]"
            var py_code = python_code_for_column_reorder(instructions.df, formattedCols, instructions.start)
            executePythonInBackground(Jupyter.notebook, py_code)
            break;

        case "backend_info":
          var info_backend = e.info_backend;
          backendManager.updateBackendParameters(info_backend["text/plain"].slice(1, info_backend["text/plain"].length - 1));
          break;

        case "tooltip":
          executePythonInBackground(Jupyter.notebook, python_code_for_info())
            .then((out) => {
              if (out.msg_type === "execute_result") {
                var info = out.content.data["text/plain"];
                backendManager.updateBackendParameters(info.slice(1, info.length - 1));
              } else {
                // something else has been done in background or ERROR!
              }
            })
          break;

        case "on_login":
          credentials_login = e.credentials;
          token_login = e.token;
          break;

        case "steps_application":
          executePythonInBackground(Jupyter.notebook, `${MSTR_ENV_VARIABLE_NAME} = create_custom_env()`, true).then(() => {
            applySteps(MSTR_ENV_VARIABLE_NAME, Jupyter.notebook, e.steps).then(() => {
              var df_converters = e.selectedDataframes.map(({ dfName, selectedObjects }) => {
                var py_code = python_code_for_dataframe_columns_selection(MSTR_ENV_VARIABLE_NAME, selectedObjects, dfName);
                return executePythonInBackground(Jupyter.notebook, py_code, true);
              });
              Promise.all(df_converters).then(() => {
                backendManager.finishDataModeling(true);
              });
            });
          });
          break;

        default:
          break;
      }
    };

    $("<iframe/>")
      .attr({src: connector_address + snippet_for_loading, id: "mstr_iframe"})
      .appendTo(mstr_editor);

    return mstr_editor;
  }

  function show_mstr_editor_modal() {
    modal = dialog
      .modal({
        show: false,
        notebook: Jupyter.notebook,
        keyboard_manager: Jupyter.notebook.keyboard_manager,
        body: build_mstr_editor()
      })
      .attr("id", "mstr_modal");

    modal.modal("show");
  }

  function load_jupyter_extension() {
    return Jupyter.notebook.config.loaded.then(() => {
      initialize();
    });
  }

  return {
    load_jupyter_extension: load_jupyter_extension,
    load_ipython_extension: load_jupyter_extension
  };
});

// global (for MSTRIO) functionalities required from top level
function lastElement(iterableObject, indexOff = 0) {
  try {
    if (indexOff < 0) indexOff = -indexOff;
    if (indexOff > iterableObject.length - 1) indexOff = 0;
    return iterableObject[iterableObject.length-1-indexOff];
  }
  catch (e) {
    console.log(e);
    return undefined;
  }
}

function appendHead(file, which_document = null) {
  var src = `${origin}/nbextensions/mstr_jupyter/${file}`;

  switch (lastElement(file.split('.'))) {
    case 'js':
      var code = window.document.createElement("script");
      code.setAttribute("src", src);
      code.setAttribute("rel", "prefetch");
      code.setAttribute("type", "text/javascript");
      window.document.head.appendChild(code);
    break;
    case 'css':
      var code = window.document.createElement("link");
      code.setAttribute("href", src);
      code.setAttribute("rel", "stylesheet");
      code.setAttribute("type", "text/css");

      if (which_document == null) window.document.head.appendChild(code);
      else which_document.head.appendChild(code);
    break;
    default:
      console.log("Wrong file name as input. Impossible to append.");
    break;
  }
}
