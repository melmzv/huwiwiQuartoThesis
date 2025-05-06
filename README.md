# A reproducible Quarto-based template for thesis at HU Berlin’s School of Business and Economics

## Why use this template?

This repository provides a modern, modular Quarto + LaTeX template tailored to students writing empirical theses—especially within the Institute of Accounting and Auditing and the Finance Group at Humboldt-Universität zu Berlin. The template is fully compliant with the [WiWi faculty](https://www.wiwi.hu-berlin.de/de/studium/rund-um-das-studium/sb/leitfaden.pdf/@@download/file/Leitfaden.pdf) and [Institute of Accounting and Auditing](https://www.wiwi.hu-berlin.de/de/professuren/bwl/rwuwp/teaching/guidelines_mt_aug2024.pdf) formatting guidelines—just clone the repo and render the template! :sparkles:

This template was developed as part of advanced empirical coursework (see my profile for completed projects), specifically for a replication and extension study that followed open science principles while integrating programming skills and institutional knowledge. Traditional empirical workflows often involve manual data collection, fragmented scripts, and disconnected reporting, which makes reproducibility and collaboration difficult. This template, based on the TRR 266 Template for Reproducible Empirical Accounting Research (TREAT), addresses those challenges by offering a reproducible, modular workflow.

The default branch, `main`, is a stripped-down version of the template containing only the Python workflow. This branch was cloned initially from the TREAT repository, focusing solely on the Python workflow and utulizing the Python libraries listed in the `requirements.txt` file.

## Why use Quarto?

Quarto enables seamless integration of code, narrative, and output in a single document, making it a powerful alternative to traditional LaTeX-only workflows. Unlike LaTeX, which often requires separate tools and manual steps to embed code results, Quarto allows you to combine Python or R code, plots, regression tables, and formatted text in one source.

This makes it ideal for empirical research where transparency, version control, and automation are essential. By choosing Quarto, you benefit from a modern and flexible writing system that ensures your analysis is fully transparent and reproducible—from raw data to final PDF.

Still not impressed? You might want to read [this blog post by Guillaume Dehaene](https://www.guillaumedehaene.com/posts/2024/03/quarto_is_better.html), which explains why **"Quarto is better"** for modern academic workflows.

> *Why not just use Overleaf?*  

- While Overleaf is a convenient cloud-based platform with Git integration and real-time collaboration, it is still limited by its reliance on an internet connection and browser performance, and its servers can occasionally experience downtime. :zap:
- Plus, Zotero integration-necessary for managing references—is only available for **premium users**. And let’s be honest: we’d rather not pay for something we can do better locally. :money_with_wings:

Take a look at useful VS Code extensions that can enhance your Quarto experience below :point_down:

<p align="center">
  <img src="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExemdyZWZiM2J5YnhxYXVmdmlwdmxpbGZnMHdyNXhjOGlkcTRydGRncSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xT3i1kd2xAVSKslyh2/giphy.gif" alt="Centered GIF"/>
</p>

### Where do I start?

> *"Talk is cheap. Show me the code."*  
> — **Linus Torvalds**

You start by setting up a few tools on your system: 

- If you are new to Python, follow the [Real Python installation guide](https://realpython.com/installing-python/) that gives a good overview of how to set up Python on your system.

- Additionally, you will need to set up an Integrated Development Environment (IDE) or a code editor. We recommend using VS Code; please follow the [Getting started with Python in VS Code Guide](https://code.visualstudio.com/docs/python/python-tutorial).

- You wll also need [Quarto](https://quarto.org/), a scientific and technical publishing system used for used for documenting this project. Please follow the [Quarto installation guide](https://quarto.org/docs/get-started/) to install Quarto on your system. I recommend downloading the Quarto [Extension](https://marketplace.visualstudio.com/items?itemName=quarto.quarto) for enhanced functionality, which streamlines the workflow and ensures professional documentation quality for this project. You can find out more about the system [here](https://quarto.org/).

- To render this Quarto thesis template to PDF, you need to have both **Quarto** and a full **LaTeX distribution** installed on your local machine.  
  - For MacOS users, we recommend installing TeX Live via Homebrew.  
  - For Windows or Linux, visit [TeX Live](https://www.tug.org/texlive/acquire-netinstall.html) or [TinyTeX](https://yihui.org/tinytex/) for lightweight alternatives.

- Finally, you will also need to have `make` installed on your system, if you want to use it. It reads instructions from a `Makefile` and helps automate the execution of these tasks, ensuring that complex workflows are executed correctly and efficiently.
    - For Linux users this is usually already installed. 
    - For MacOS users, you can install `make` by running `brew install make` in the terminal. 
    - For Windows users, there are few options to install `make` and they are dependent on how you have setup your system. For example, if you have installed the Windows Subsystem for Linux (WSL), you can install `make` by running `sudo apt-get install make` in the terminal. If not, you are probably better off googling how to install `make` on Windows and follow a reliable source.


:open_file_folder: Next, explore the repository to familiarize yourself with its folders and their contents:

- `config`: This directory holds configuration files that are being called by the program scripts in the `code` directory. We try to keep the configurations separate from the code to make it easier to adjust the workflow to your needs. In this project, `pull_data_cfg.yaml` file outlines the variables and settings needed to extract the necessary data from the WRDS databases. The `prepare_data_cfg.yaml` file specifies the configurations for preprocessing and cleaning the data before analysis, ensuring consistency and accuracy in the dataset and following the paper filtration requirements. The `do_analysis_cfg.yaml` file contains parameters and settings for performing the final analysis on the extracted earnings data.

- `code`: This directory holds program scripts used to pull data from WRDS directly using python, prepare the data, run the analysis and create the output files (a replicated (pickle) output). Using pickle instead of Excel is more preferable as it is a more Pythonic data format, enabling faster read and write operations, preserving data types more accurately, and providing better compatibility with Python data structures and libraries. 
<p align="center">
  <img src="https://miro.medium.com/v2/resize:fit:1100/format:webp/1*eFuMBvt4HtOK1YFb-SQ2KA.png" alt="Pickling process illustration" width="400">
</p>

*The picture illustrates the process of serializing Python objects into a binary format (pickling) for storage in a file and deserializing them back into Python objects (unpickling) for reuse in analysis or other workflows.*

- `data`: A directory where data is stored. It is used to organize and manage all data files involved in the project, ensuring clear separation between external, pulled, and generated data. Go through the sub-directories and a README file that explains their purpose. 

- `doc`: This directory contains Quarto files (.qmd) that include text and program instructions for the paper and presentation (feel free to use the presentation template and adjust it to your needs). These files are rendered through the Quarto process using Python and the VS Code extension, integrating code, results, and literal text seamlessly.

> **🌳 Tip:** To easily present your thesis directory structure (e.g., to your supervisor), you can copy and paste it directly from within VS Code using the [Extension](https://marketplace.visualstudio.com/items?itemName=Fuzionix.file-tree-extractor&ssr=false#overview).

> [!TIP]
> - Download the [VSCode Extension](https://marketplace.visualstudio.com/items?itemName=axelrindle.duplicate-file) for duplicating files. This will streamline your workflow by allowing you to duplicate files directly within Visual Studio Code, rather than manually copying and pasting in Finder (Mac) or File Explorer (Windows). :wink:
> - Another fresh tip to synchronise vertical or horizontal scrolling in splitted view in VS Code. To enable it, type in the Command Palette the action name `Toggle Locked Scrolling Across Editors`. This is particularly useful when aligning the config file with the corresponding Python file, for example. :woman_technologist:
> - Here is a new tip for [references.bib](doc/references.bib) file! If you're working with multiple citation formats, consider setting up Zotero's Quick Copy feature to directly copy BibTeX-formatted references into the `bib` file. This can save time and ensure consistency in your bibliography. Learn more about the Quick Copy feature :point_right: [here](https://www.zotero.org/support/creating_bibliographies#quick_copy).
> - If the project requires word count, use the [VSCode Extension](https://marketplace.visualstudio.com/items?itemName=yunierolivera.markdown-quarto-word-count#:~:text=To%20use%20this%20extension%2C%20open,type%20Markdown%20%26%20Quarto%20Word%20Count%20.) to display the word count in the status bar. Very convenient! 
> - Use the [Data Wrangler Extension](https://code.visualstudio.com/docs/datascience/data-wrangler#:~:text=Data%20Wrangler%20is%20a%20code,clean%20and%20transform%20the%20data.) to view and analyze the pulled data, show column statistics and visualizations. It is particularly useful, if  your computer can not manage large-sized pulled CSVs.

> [!NOTE]
> ✨ This template also includes standalone `.tex` files—[`abstract.tex`](doc/abstract.tex), [`abbreviations.tex`](doc/abbreviations.tex), and [`acknowledgments.tex`](doc/acknowledgements.tex)—which can be used if your chair requires a **different section order** than the default set by the Institute of Accounting and Auditing. Read more on the partials [here](https://quarto.org/docs/journals/templates.html).
> For example, some chairs may prefer to place the abstract **before** the table of contents, or include the list of abbreviations as a main section. Simply amend Quarto YAML preamble and adjust the order to fit your needs. This makes the template highly adaptable across different thesis styles.
> :point_right: First, in order to display and work with Latex 'tex' files, download the [LaTeX Workshop Extension](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop) for VS Code. This extension provides a comprehensive set of tools for editing and compiling LaTeX documents, including syntax highlighting, code completion, and PDF preview capabilities.


You also see an `output` directory but it is empty. Why? Because the output paper and presentation are created locally on your computer.


### How do I create the output?

Assuming that you have database (WRDS in this example) access, Python, VS Code, Quarto, and `make` installed, this should be relatively straightforward. Refer to the setup instructions in the section [above](#where-do-i-start).

1. Click on the `Use this template` button on the top right of the repository and choose `Create a new repository`. Provide the repository with a name, a description, and select whether it should be public or private. Then click `Create repository`.
2. Clone the repository to your local machine. Open the repository in VS Code and launch a new terminal.
3. It is advisable to create a virtual environment for the project:

```shell
python3 -m venv venv # Run this command in the terminal to create a virtual environment in the `venv` directory.
source venv/bin/activate # Activate the virtual environment on Linux or macOS.
# venv\Scripts\activate.bat # If you are using Windows Command Prompt.
# venv/Script/Activate.ps1 # If you are using Windows PowerShell and have allowed script execution.
```
You can deactivate the virtual environment by running `deactivate`.

4. With an active virtual environment, you can install the required packages by running `pip install -r requirements.txt` in the terminal. This will install the required packages for the project in the virtual environment.
5. Copy the file `_secrets.env` to `secrets.env` in the project main directory. Then edit the `secret.env` by adding your WRDS credentials.

> [!CAUTION]
> Ensure your database credentials are stored securely in `secrets.env`. Sharing this file or exposing its contents could compromise access to sensitive data.

> [!NOTE]
> First time you run the `pull_wrds_data.py` script, it will ask you to enter your WRDS credentials. You should enter them again and choose `y` to save the `.pgpass` file. This will save your credentials in the `.pgpass` file so that you do not need to enter them again.
> Note that inability to see the password while typing is standard behavior for security reasons. When prompted, type your password even though it won’t be displayed and press Enter. When WRDS prompts you to create a .pgpass file, it’s asking if you want to store your login credentials for easier future access. Answer ‘y’ to create the file now and follow the instructions, or ‘n’ if you prefer to enter your password each time or create the file manually later.

> [!TIP]
> I have included an intermediate check step using the `code/python/test_wrds_connection.py` file to ensure that WRDS access is secure and functional before running the main program script. Run it first to ensure the connection to WRDS has been successful.
6. Run `make all` in the terminal. I use the [Makefile Tools extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode.makefile-tools) in VS Code to run the makefile and create the necessary output files to the `output` directory.
I highly recommend using the Makefile! Otherwise, you can run the following commands in the terminal:

```shell
python code/python/pull_wrds_data.py
python code/python/prepare_data.py
python code/python/do_analysis.py
quarto render doc/paper.qmd
mv doc/paper.pdf output
rm -f doc/paper.ttt doc/paper.fff
quarto render doc/presentation.qmd
mv doc/presentation.pdf output
rm -f doc/presentation.ttt doc/presentation.fff
```
7. Eventually, you will be greeted with the two files in the `output` directory: "paper.pdf" and "presentation.pdf". You have successfully used an open science resource and reproduced the analysis. Congratulations! :rocket:

### Setting up for Reproducible Empirical Research

This code base, adapted from TREAT, should give you an overview on how the template is supposed to be used for a thesis project.

> **📌 Note:** This repository does not contain any **pull requests** because it is an individual project without ongoing code reviews or feature-based branching workflows. However, it includes a **release** after project finish, allowing future collaborative research to build upon this work. 

To start a new reproducible thesis project, follow these steps: 
1. Clone the repository by clicking “Use this Template” at the top of the file list on GitHub. 
2. Remove any files that you don’t need for your specific project. 
3. Over time, you can fork this repository and customize it to develop a personalized template that fits your workflow and preferences.


### Licensing

This project utilizes the template used in collaborative research center [TRR 266 Accounting for Transparency](https://accounting-for-transparency.de), that is centered on workflows that are typical in the accounting and finance domain.

The repository is licensed under the MIT license. I would like to give the following credit:

```
This repository was built based on the ['treat' template for reproducible research](https://github.com/trr266/treat).
```

### References

:bulb: If you’re new to collaborative workflows for scientific computing, here are some helpful texts:

- Christensen, Freese and Miguel (2019): Transparent and Reproducible Social Science Research, Chapter 11: https://www.ucpress.edu/book/9780520296954/transparent-and-reproducible-social-science-research
- Gentzkow and Shapiro (2014): Code and data for the social sciences:
a practitioner’s guide, https://web.stanford.edu/~gentzkow/research/CodeAndData.pdf
- Wilson, Bryan, Cranston, Kitzes, Nederbragt and Teal (2017): Good enough practices in scientific computing, PLOS Computational Biology 13(6): 1-20, https://doi.org/10.1371/journal.pcbi.1005510