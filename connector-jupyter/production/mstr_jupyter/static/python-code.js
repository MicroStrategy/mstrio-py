/* eslint-disable max-len */
define([], () => class PythonCode {
  constructor(...args) {
    if (args.length) {
      if ('url' in args[0] || 'loginMode' in args[0]) {
        [
          this.authenticationDetails,
          this.dataframeDetails,
          this.otherDetails,
        ] = args;
      } else if ('customEnvironment' in args[0]) {
        [this.otherDetails] = args;
      } else {
        [
          this.dataframeDetails,
          this.otherDetails,
        ] = args;
      }
    }

    // workaround for Safari:
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions#Browser_compatibility
    this.generateConnectionCode = this.generateConnectionCode.bind(this);
    this.generateApplyStepsCodeInsideExport = this.generateApplyStepsCodeInsideExport.bind(this);
    this.forInitialEngine = this.forInitialEngine.bind(this);
    this.forImport = this.forImport.bind(this);
    this.forExport = this.forExport.bind(this);
    this.forUpdate = this.forUpdate.bind(this);
    this.forGettingDataframesNames = this.forGettingDataframesNames.bind(this);
    this.forGettingKernelInfo = this.forGettingKernelInfo.bind(this);
    this.forGettingPackageVersionNumber = this.forGettingPackageVersionNumber.bind(this);
    this.forGettingDataframeData = this.forGettingDataframeData.bind(this);
    this.forModelingGatheredData = this.forModelingGatheredData.bind(this);
    this.forDataframeColumnsSelection = this.forDataframeColumnsSelection.bind(this);
    this.forApplyingStep = this.forApplyingStep.bind(this);
  }


  // code preparation functions
  static code() {
    return { // static reference to available functions returning python code - for JupyterCell reference use
      forInitialEngine: {
        name: 'forInitialEngine',
        required: 'otherDetails[customEnvironment]',
      },
      forApplyingStep: {
        name: 'forApplyingStep',
        required: 'otherDetails[customEnvironment]\nargs: step [Object]',
      },
      forCredentials: {
        name: 'forCredentials',
        required: 'authenticationDetails[user, password]',
      },
      forImport: {
        name: 'forImport',
        arguments: 'includeCredentials = false',
        required: 'authenticationDetails[user, password, envUrl, loginMode]\ndataframeDetails[name, projectId, datasetType, datasetId, body]',
      },
      forExport: {
        name: 'forExport',
        arguments: 'includeCredentials = false',
        required: 'authenticationDetails[user, password, envUrl, loginMode]\ndataframeDetails[projectId, selectedDataframes]\notherDetails[saveAsName, description, certify, folderId, customEnvironment]',
      },
      forUpdate: {
        name: 'forUpdate',
        arguments: 'includeCredentials = false',
        required: 'authenticationDetails[user, password, envUrl, loginMode]\ndataframeDetails[projectId, datasetId]\notherDetails[updatePolicies, customEnvironment]',
      },
      forGettingDataframesNames: {
        name: 'forGettingDataframesNames',
        required: 'none',
      },
      forGettingKernelInfo: {
        name: 'forGettingKernelInfo',
        required: 'none',
      },
      forGettingPackageVersionNumber: {
        name: 'forGettingPackageVersionNumber',
        required: 'none',
      },
      forGettingDataframeData: {
        name: 'forGettingDataframeData',
        required: 'dataframeDetails[name]\n(optional)otherDetails[rows]',
      },
      forModelingGatheredData: {
        name: 'forModelingGatheredData',
        required: 'dataframeDetails[name]\n(optional)otherDetails[rows]',
      },
      forDataframeColumnsSelection: {
        name: 'forDataframeColumnsSelection',
        required: 'dataframeDetails[selectedObjects, name]\notherDetails[customEnvironment]',
      },
    };
  }

  static capitalize(string) {
    return (
      !string
        ? ''
        : string.charAt(0).toUpperCase() + string.slice(1)
    );
  }

  static oneLine(multilinePythonCode) {
    return (
      !multilinePythonCode
        ? ''
        : multilinePythonCode.trim()
          .replace(/\n/gi, ' ')
          .replace(/\s{2,}/gi, ' ')
    );
  }
  // ---

  generateConnectionCode(forEndUser = false, forExport = false) {
    const { url, username = '', loginMode, identityToken } = this.authenticationDetails;
    const { projectId, datasetType } = this.dataframeDetails;
    const whetherIsReportCode = datasetType && datasetType.toLowerCase() === 'report'
      ? 'from mstrio.project_objects.report import Report'
      : 'from mstrio.project_objects.datasets.cube import load_cube';
    const datasetTypeImportString = forExport
      ? 'from mstrio.project_objects.datasets.super_cube import SuperCube'
      : whetherIsReportCode;
    const importCode = `
from mstrio.connection import Connection
${datasetTypeImportString}
from getpass import getpass
    `.trim();

    const credentialsCode = forEndUser
      ? `
mstr_username = input("Username: ")
mstr_password = getpass("Password: ")
mstr_login_mode = input("Login mode (1 - Standard, 16 - LDAP) [1]: ") or 1
      `.trim()
      : `
mstr_identity_token = "${identityToken}"
mstr_login_mode = ${loginMode || 'None'}
      `.trim();

    const authCode = `
mstr_base_url = "${url}"
mstr_project_id = "${projectId}"
${credentialsCode}
    `.trim();

    const usernameCodePart = username ? `"${username}"` : 'None';
    const connectionCode = forEndUser
      ? 'mstr_connection = Connection(mstr_base_url, mstr_username, mstr_password, project_id=mstr_project_id, login_mode=mstr_login_mode)'
      : `mstr_connection = Connection(mstr_base_url, ${usernameCodePart}, project_id=mstr_project_id, identity_token=mstr_identity_token, login_mode=mstr_login_mode)`;

    return `
${importCode}

# Authentication & Connection
${authCode}

${connectionCode}
    `.trim();
  }


  generateApplyStepsCodeInsideExport(steps) {
    return (
      !steps || !steps.length
        ? ''
        : `
# Data Modeling
${steps.map((step) => this.forApplyingStep(step)).join('\n')}
`
    );
  }


  forInitialEngine() {
    const { customEnvironment } = this.otherDetails;

    return (`
import pandas as pd

def create_custom_env():
    output={}
    for el in globals().keys():
        if el[0]!='_' and isinstance(globals()[el], pd.core.frame.DataFrame):
            output[el] = globals()[el]
    return output


def update_custom_env():
    global ${customEnvironment}
    new_${customEnvironment} = ${customEnvironment}
    for el in globals().keys():
        if el[0]!='_' and isinstance(globals()[el], pd.core.frame.DataFrame) and not el in new_${customEnvironment}.keys():
            new_${customEnvironment}[el] = globals()[el]
    return new_${customEnvironment}
    `).trim();
  }

  forImport(forEndUser = false) {
    const { name, datasetType, datasetId, body: { attributes, metrics, filters }, instanceId } = this.dataframeDetails;

    const variableName = `${/\d/gi.test(name[0]) ? 'var_' : ''}${name
      .replace(/ /gi, '_')
      .replace(/[^A-Za-z0-9_]/gi, '') // NOSONAR
      }`;

    const method = datasetType && datasetType.toLowerCase() === 'report' ? 'Report' : 'load_cube';
    const connectionCode = this.generateConnectionCode(forEndUser);
    const instanceIdConverted = instanceId ? `"${instanceId}"` : 'None';
    const instanceIdCode = forEndUser ? '' : `, instance_id=${instanceIdConverted}`;

    const filtersConverted = filters.length > 0 ? JSON.stringify(filters) : 'None';
    const applyFiltersContent = attributes.length + metrics.length + filters.length === 0
      ? 'attributes = None, metrics = None, attr_elements = None'
      : `
  attributes = ${JSON.stringify(attributes)},
  metrics = ${JSON.stringify(metrics)},
  attr_elements = ${filtersConverted}
`;
    const applyFiltersCode = `${variableName}.apply_filters(${applyFiltersContent})`;

    return (`
${connectionCode}

# Data Import
${variableName} = ${method}(mstr_connection, "${datasetId}"${instanceIdCode})
${applyFiltersCode}
${variableName}.to_dataframe()
${variableName}_df = ${variableName}.dataframe

# Data Display
${variableName}_df
    `).trim();
  }


  forExport(forEndUser = false) {
    const { selectedDataframes } = this.dataframeDetails;
    const { saveAsName, description, certify, folderId, customEnvironment, dataModelingSteps = [] } = this.otherDetails;

    const tablesCode = selectedDataframes.map(({ name, attributes, metrics }) => `
mstr_dataset.add_table(
  name="${name}",
  data_frame=${customEnvironment}['${name}'],
  update_policy="replace",
  to_metric=${metrics.length ? JSON.stringify(metrics) : 'None'},
  to_attribute=${attributes.length ? JSON.stringify(attributes) : 'None'}
)
    `.trim())
      .join('\n');

    const connectionCode = this.generateConnectionCode(forEndUser, true);
    const modelingStepsCode = forEndUser ? this.generateApplyStepsCodeInsideExport(dataModelingSteps) : '';
    const descriptionConverted = description ? `, description="${description}"` : '';

    return (`
${connectionCode}
update_custom_env()
${modelingStepsCode}
# Data Export
mstr_dataset = SuperCube(mstr_connection, name="${saveAsName}"${descriptionConverted})
${tablesCode}
mstr_dataset.create(folder_id="${folderId}", force="True")
${certify ? 'mstr_dataset.certify()' : ''}
    `).trim();
  }


  forUpdate(forEndUser = false) {
    const { datasetId } = this.dataframeDetails;
    const { updatePolicies, customEnvironment, dataModelingSteps = [] } = this.otherDetails;

    const tablesCode = updatePolicies.map(({ tableName, updatePolicy }) => PythonCode.oneLine(`
mstr_dataset.add_table(name="${tableName}",
  data_frame=${customEnvironment}['${tableName}'],
  update_policy="${updatePolicy}")
`))
      .join('\n');

    const connectionCode = this.generateConnectionCode(forEndUser, true);
    const modelingStepsCode = forEndUser ? this.generateApplyStepsCodeInsideExport(dataModelingSteps) : '';

    return (`
${connectionCode}
update_custom_env()
${modelingStepsCode}
# Data Update
mstr_dataset = SuperCube(mstr_connection, id="${datasetId}")
${tablesCode}

mstr_dataset.update()
    `).trim();
  }


  forGettingDataframesNames() {
    return (`
import pandas as pd

dataframe_names=[]
for el in dir():
  if isinstance(locals()[el], pd.core.frame.DataFrame) and el[0]!='_' and locals()[el].empty == False:
      dataframe_names.append(el)

import_string = ""
for df_name in dataframe_names:
  import_string += '{"name":"' + df_name + '","rows":' + str(eval(df_name + '.shape[0]')) + ',"columns":' + str(eval(df_name + '.shape[1]')) + '},'

"[" + import_string[0:len(import_string) - 1] + "]"
  `).trim();
  }

  // TODO: recreate information about path to Python
  // Windows: !where python
  // UNIX: !which python
  forGettingKernelInfo() {
    const versionConverter = PythonCode.oneLine(`
'{"Jupyter Version":"' + str(i1[0]).replace(" ", "").replace(",", " - ").replace("\\\\", "").replace("'", "") +
'","Python Version":"' + str(i2[0]).replace("\\\\", "").replace("'", "") + '"}'
    `);
    return (`
i1 = !jupyter --version
i2 = !python --version
${versionConverter}
  `).trim();
  }


  forGettingPackageVersionNumber() {
    return (`
from mstrio import __version__ as mstrio_version
mstrio_version
  `).trim();
  }


  forGettingDataframeData() {
    const { name } = this.dataframeDetails;
    const { rows = 10 } = (this.otherDetails || {});

    return `${name}[:${rows}].to_json(orient='records')`;
  }


  forModelingGatheredData() {
    const { name } = this.dataframeDetails;
    const { rows = 10 } = (this.otherDetails || {});

    return (`
from mstrio.utils.model import Model

arg_for_model = [{'table_name': 'selected_df', 'data_frame': ${name}[:${rows}]}]
model = Model(tables=arg_for_model, name='preview_table_types', ignore_special_chars=True)

model.get_model()
    `).trim();
  }


  forDataframeColumnsSelection() {
    const { selectedObjects, name } = this.dataframeDetails;
    const { customEnvironment } = this.otherDetails;

    return (`
cols_to_leave = ${JSON.stringify(selectedObjects)}
final_cols = [name for name in ${customEnvironment}['${name}'].columns if name not in cols_to_leave]
${customEnvironment}['${name}'] = ${customEnvironment}['${name}'].drop(columns=final_cols)
    `).trim();
  }


  forApplyingStep(step) {
    const { customEnvironment } = this.otherDetails;
    const { type, oldName, newName, dfName = '' } = step;

    switch (type) {
      case 'RENAME_DF':
        return (`
${customEnvironment}['${newName}'] = ${customEnvironment}['${oldName}']
del ${customEnvironment}['${oldName}']
        `).trim();
      case 'RENAME_OBJ':
        return (`
${customEnvironment}['${dfName}'] = ${customEnvironment}['${dfName}'].rename(columns = {'${oldName}': '${newName}'})
        `).trim();
      default: return '';
    }
  }
});
