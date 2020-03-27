/*jshint esversion: 6*/

function changeSize(mode, element) {
  switch (mode) {
    case 'authentication':
    case 'loading':
      element.style.maxWidth = '538px'; element.style.maxHeight = '661px';
      break;
    case 'project-selection':
      element.style.maxWidth = '538px'; element.style.maxHeight = '706px';
      break;
    default:
      element.style.maxWidth = '1350px'; element.style.width = '80%'; element.style.maxHeight = '850px';
      break;
  }
}

function checkImportExport(snippet, flag) {
  if (!isImportingExporting(snippet, flag)) {
    clearInterval(localStorage.getItem("interval_var"));
    localStorage.removeItem("interval_var");

    flag = false;
    window.backendManager.toggleImportOrExportInProgress(false);
  }
}

function isImportingExporting(snippet, flag) {
  try {
    var cells = document.getElementById("notebook-container").getElementsByClassName("cell");

    for (var i = 0; i < cells.length; i++) {
      var title = cells[i].getElementsByClassName("input_prompt")[0];
      var input = cells[i].getElementsByClassName("input_area")[0];

      if (input.innerText.substring(0, snippet.length + 7) == "# code " + snippet) {
        if (flag === true && title.innerText.indexOf("*") < 0) return false;
        else return true;
      }
    }
  }
  catch (e) { console.log(e) }
}

function callback_object(output_function, shell_reply_function) {
  /* This is object related to Jupyter Kernel
   * When used as second argument in Jupyter.notebook.kernel.execute, you can control what happens with output of python code
   * @param [output_function] {FUNCTION w/ 1 parameter} preferable form: (out) => {// code what to do with {out} //}
   * @param [shell_reply_function] {FUNCTION w/ 1 parameter} preferable form: (out) => {// code what to do with {out} //}
   */
  if (output_function === undefined) output_function = () => {};
  if (shell_reply_function === undefined) shell_reply_function = () => {};
  return {
    shell: {
      reply: shell_reply_function
    },
    iopub: {
      output: output_function,
      clear_output: () => {}
    },
    input: () => {},
    clear_on_done: true
  }
}

// docs: https://jupyter-client.readthedocs.io/en/stable/messaging.html
var available_msg_type = {
  // expected and wanted:
  stream: 'stream',
  execute_result: 'execute_result',

  // unexpected (no mstrio code should expect it):
  display_data: 'display_data',
  update_display_data: 'update_display_data',
  execute_input: 'execute_input',

  // erroneous:
  error: 'error',
};

function executePythonInBackground(jupyter_notebook, python_code, shell_only) {
  /* In order to understand how does the function work and what is the callback output object
   * fire up any python code in this function in the following way:
   * executePythonInBackground(Jupyter.notebook, "print('xD')").then((out) => {console.log(out)})
   * and see how the {out} object look in console
   */
  var accepted_statuses = [
    available_msg_type.stream,
    available_msg_type.execute_result,
  ];

  return new Promise(function(resolve, reject) {
    var callback;
    if (!shell_only) {
      callback = callback_object(
        (out) => {
          if (accepted_statuses.includes(out.msg_type)) resolve(out);
          else {
            console.log(out.content);
            reject(out);
          }
        },
        () => {},
      );
    } else {
      callback = callback_object(
        () => {},
        (out) => {
          if (out.msg_type === 'execute_reply' && out.content.status === 'ok') resolve(out);
          else {
            console.log(out.content);
            reject(out);
          }
        },
      );
    }
    jupyter_notebook.kernel.execute(python_code, callback, {silent: false})
  });
}

function execute_credentials_kernel_background(user, password) {
  executePythonInBackground(Jupyter.notebook, python_code_for_credentials(user, password));
}

function applySteps(custom_env, jupyter_notebook, steps, index = 0) {
  if (index >= steps.length || index < 0) {
    return Promise.resolve(true);
  };
  var step = steps[index];
  var py_code;
  switch (step.type) {
    case 'RENAME_DF': // renaming dataframe
      py_code = `${custom_env}['${step.newName}'] = ${custom_env}['${step.oldName}']\ndel ${custom_env}['${step.oldName}']\n`;
      break;
    case 'RENAME_OBJ': // renaming attribute or metric in specific dataframe
      py_code = `${custom_env}['${step.dfName}'] = ${custom_env}['${step.dfName}'].rename(columns = {'${step.oldName}': '${step.newName}'})\n`;
      break;
    default: applySteps(custom_env, jupyter_notebook, steps, index + 1);
      break;
  }
  return executePythonInBackground(jupyter_notebook, py_code, true).then(() => {
    return applySteps(custom_env, jupyter_notebook, steps, index + 1)
  });
}
