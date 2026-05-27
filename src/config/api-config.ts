import axios, { CreateAxiosDefaults } from "axios";
import * as vscode from "vscode";

const config = vscode.workspace.getConfiguration("patterngen");
const ragBaseUrl = config.get<string>("ragEndpoint");

const axiosConfig: CreateAxiosDefaults = {
	baseURL: ragBaseUrl,
};

const ragApi = axios.create(axiosConfig);

export default ragApi;
