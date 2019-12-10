/*jshint esversion: 6*/
function changeSize(mode, element) {
  console.log(`MODE: ${mode}`);
  switch (mode) {
    case 'authentication': element.style.maxWidth = '538px'; element.style.maxHeight = '661px';
      break;
    case 'project-selection': element.style.maxWidth = '538px'; element.style.maxHeight = '706px';
      break;
    case 'browsing': element.style.maxWidth = '1350px'; element.style.width = '80%'; element.style.maxHeight = '850px'; 
      break;
    case 'filter-selection': element.style.maxWidth = '1235px'; element.style.maxHeight = '800px'; 
      break;
    case 'export-select': element.style.maxWidth = '854px'; element.style.maxHeight = '602px'; element.style.width = '90%';
      break;
    case 'export-dir-select': element.style.maxWidth = '1235px'; element.style.maxHeight = '800px'; element.style.width = '90%';
      break;
    case 'export-data-wrangler': element.style.maxWidth = '1300px'; element.style.width = '90%'; element.style.maxHeight = '780px'; 
      break;
    default:
      break;
  }
}

function checkImportExport(snippet, flag) {
  if (!isImportingExporting(snippet, flag)) {
    console.log(`${snippet} Process Finished`); 
    clearInterval(localStorage.getItem("interval_var"));
    localStorage.removeItem("interval_var");

    flag = false;
    document.getElementById("mstr_iframe").contentWindow.backendManager.toggleImportOrExportInProgress(false);
  } 
}

function isImportingExporting(snippet, flag) {
  try {
    var cells = document.getElementById("notebook-container").getElementsByClassName("cell");

    for (var i = 0; i < cells.length; i++) {
      var title = cells[i].getElementsByClassName("input_prompt")[0];
      var input = cells[i].getElementsByClassName("input_area")[0];

      if (input.innerText.substring(0, snippet.length) == "# code " + snippet) {
        if (flag === true && title.innerText.indexOf("*") < 0) return false;
        else return true;
      }
    }
  }
  catch (e) { console.log(e) }
}

function callback_object(out_function) {
  /* This is object related to Jupyter Kernel
   * When used as second argument in Jupyter.notebook.kernel.execute, you can control what happens with output of python code
   * @param [out_function] {FUNCTION w/ 1 parameter} preferable form: (out) => {// code what to do with {out} //}
   */
  return {
    shell: {
      reply: () => {}
    },
    iopub: {
      output: out_function,
      clear_output: () => {}
    },
    input: () => {},
    clear_on_done: true
  }
}

function executePythonInBackground(jupyter_notebook, python_code, callback_function) {
  /* In order to understand how does the function work and what is the callback output object
   * fire up any python code in this function in the following way:
   * executePythonInBackground(Jupyter.notebook, "print('xD')", (out) => {console.log(out)})
   * and see how the {out} object look in console
   */
  if (callback_function === undefined) {callback_function = (out) => {}}
  var callback = callback_object(callback_function)
  jupyter_notebook.kernel.execute(python_code, callback, {silent: false})
}

function execute_credentials_kernel_background(user, password) {
  executePythonInBackground(Jupyter.notebook, python_code_for_credentials(user, password));
}
