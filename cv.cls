\LoadClassWithOptions{article}  % build on standard article class

% set page dimensions
\usepackage{geometry}
\geometry{
    left=0.75in,
    right=0.75in,
    top=0.9in,
    bottom=0.75in,
    headsep=0.2in,
}

% add headers
\usepackage{fancyhdr}
\pagestyle{fancy}

% custom header on the first page
\fancypagestyle{firstpage}{
    % headers
    \lhead{}
    \chead{}
    \rhead{\footnotesize updated: \today}
    \renewcommand{\headrulewidth}{0pt} % remove line under header
    % and the footers
    \lfoot{}
    \cfoot{}
    \rfoot{}
}

% load other useful packages
\usepackage[dvipsnames]{xcolor}
\usepackage[hidelinks, colorlinks=true, allcolors=NavyBlue]{hyperref}
\usepackage{etaremune}
\usepackage{microtype}
\usepackage{parskip}

% this command just comments out (or hides) anything inside
\newcommand{\hide}[1]{}

% commands for common links
\newcommand{\link}[2]{(\href{#1}{#2})}
\newcommand{\github}[1]{\link{#1}{Github}}
\newcommand{\pypi}[1]{\link{#1}{PyPI}}
\newcommand{\ads}[1]{\link{#1}{ADS}}

% command to set a page title
\setcounter{secnumdepth}{0} % remove section numbers
\newcommand{\pagetitle}[1]{\section{{\LARGE \bf{#1}}} {\rule{\linewidth}{0.5mm}}}

% cv sections are wrapped in the llist environment
% uses \sectiontitle{title} to make the title in the margin
% section text begins on next line if title is too long
% I don't understand all of this code
\def\@tablebox#1{\begin{tabular}[t]{lr}#1\end{tabular}}
\newbox\@title
\newenvironment{llist}
    {
        \begin{list}
            {} % labeling
            { % spacing
                \setlength\labelwidth{1.05in}
                \setlength\leftmargin{1.1in}
                \def\sectiontitle##1{
                    \setbox\@title=\hbox{{\bf\@tablebox{##1}}}\dp\@title=0pt
                    \item[\copy\@title]\ifdim\wd\@title>\labelwidth\leavevmode \\* \else \fi
                }
                \def\makelabel##1{##1\hfill}
            }
    }
    {
        \end{list}
    }

% define the info box
\newcommand{\infobox}[2]{
    \vspace{-0.2cm} \newline
    \begin{minipage}{0.5\textwidth}
        #1
    \end{minipage}
    \begin{minipage}{0.49\textwidth}
        \begin{flushright}
            #2
        \end{flushright}
    \end{minipage} 
    \hfill
    \vspace{0.25cm} \newline
    \rule{\linewidth}{0.5mm}
    \vspace{-0.4cm}
}

% define cvsection
% first argument is the section title
% second argument is the section body
\newcommand{\cvsection}[2]{
    \begin{llist}
        \sectiontitle{#1} 
        
        #2
    \end{llist}
}

% determine font for the cvitem title
% first argument is the title
% second argument is the date
% third argument is the body
% if third argument present, title is smallcaps
% if not, regular text with hanging indent
\newcommand{\cvitemtitle}[3]{
    \ifx&#3& % if #3 is empty
        \hangindent=2mm #1
    \else % if #3 is not empty
        \textsc{#1}
    \fi
}

% determine format of cvitem head
% first argument is the title
% second argument is the date
% third argument is the body
% if second argument present, head split for title and date
% if not, title given more horizontal space
\newcommand{\cvitemhead}[3]{
    \ifx&#2& % if #2 is empty
        \begin{minipage}[t]{0.95\linewidth}
            \cvitemtitle{#1}{#2}{#3}
        \end{minipage}
    \else % if #2 is not empty
        \begin{minipage}[t]{0.82\linewidth}
            \cvitemtitle{#1}{#2}{#3}
        \end{minipage} \hfill
        \begin{minipage}[t]{0.16\linewidth}
            \raggedleft #2
        \end{minipage}
    \fi
    \parfillskip0pt
}

% finally, define a cvitem!
% first argument is the title
% second argument is the date
% third argument is the body
% see the descriptions of cvitemtitle and cvitemhead above
% to understand how this command changes if arguments 2 and 3
% are present or not
\newcommand{\cvitem}[3]{
    \ifx&#3& % if #3 is empty
        \begin{minipage}[t]{\linewidth}
            \cvitemhead{#1}{#2}{#3}
        \end{minipage}
    \else % if #3 is not empty
        \begin{minipage}[t]{\linewidth}
            \cvitemhead{#1}{#2}{#3}
            \begin{minipage}[l]{0.82\textwidth}
                \vspace{1.5mm}
                #3
            \end{minipage}
        \end{minipage}
    \fi
}

% and one more environment for papers
% basically a wide, raggedright version of cvitem
% where the third argument is the ADS link
\newcommand{\paper}[3]{
    \begin{minipage}[t]{\linewidth}
        \cvitemhead{\raggedright #1 \\}{}{non-empty}
        \begin{minipage}[l]{0.95\textwidth}
            \vspace{1.5mm}
            \raggedright #2
            \hspace{-3.5mm} \ads{#3}
        \end{minipage}
    \end{minipage}
}
