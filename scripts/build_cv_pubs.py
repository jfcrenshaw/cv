"""Script to generate CV publication list from ADS library.

Quick start:
1. Install the ads Python library and save your ADS API token, following the
    instructions here: https://ads.readthedocs.io/en/latest/
2. Get the ID code for your ADS library, which is in the url:
    https://ui.adsabs.harvard.edu/user/libraries/<LIB_CODE>
3. Update the configs in the main() function below, at the very least including
    your library code and name. To understand other options, look at the
    docstring for the CVPubBuilder class.

Written by John Franklin Crenshaw
"""

from ads.libraries import Library  # type: ignore
from ads.search import Article  # type: ignore
from datetime import datetime


class CVPubBuilder:
    """Class to generate CV publication lists from ADS library."""

    def __init__(
        self,
        lib_code: str,
        name: str,
        name_variations: list[str] | None = None,
        primary_config: dict | None = None,
        secondary_config: dict | None = None,
        tertiary_config: dict | None = None,
        hide: set[str] | None = None,
        print_stats: bool = True,
        n_authors: int = 4,
        tex_list_env: str = "etaremune",
        tex_file: str = "sections/publications.tex",
    ) -> None:
        """Initialize the publication builder.

        Parameters:
        -----------
        lib_code : str
            The library code identifier for accessing the ADS library.
        name : str
            Your name as it will be printed in the CV.
        name_variations : list of str, optional
            A list of alternative name variations to recognize as you in
            the author lists. These are all converted to the standard name
            provided in the previous parameter. Defaults to None
        doi_overrides : dict[str, set[str]], optional
            A dictionary that allows you to override the automatic sorting
            of papers into primary, secondary, and tertiary, which is based
            on the author list. The dictionary should have three keys:
            "primary", "secondary", and "tertiary", each mapping to a set of
            DOI strings that should be categorized accordingly.
            Defaults to None
        primary_config : dict, optional
            A dictionary with keys "title", "intro", and "overrides" for the
            primary paper section. "title" is the section title, "intro" is
            an optional introductory paragraph for that section, and
            "overrides" is an optional set of DOI strings for papers that
            should be categorized as primary regardless of the author list.
            If None, "title" defaults to "First Author:",
            while "intro" and "overrides" default to None.
        secondary_config : dict, optional
            A dictionary with keys "title", "intro", and "overrides" for the
            secondary paper section. "title" is the section title, "intro" is
            an optional introductory paragraph for that section, and
            "overrides" is an optional set of DOI strings for papers that
            should be categorized as secondary regardless of the author list.
            If None, "title" defaults to "Co-Author with Major Contributions:",
            while "intro" and "overrides" default to None.
        tertiary_config : dict, optional
            A dictionary with keys "title", "intro", and "overrides" for the
            tertiary paper section. "title" is the section title, "intro" is
            an optional introductory paragraph for that section, and
            "overrides" is an optional set of DOI strings for papers that
            should be categorized as tertiary regardless of the author list.
            If None, "title" defaults to "Other Co-Author Papers:",
            while "intro" and "overrides" default to None.
        hide : set[str] or None, optional
            A set of DOI strings for papers that should be hidden entirely
            from the publication list, regardless of author list. Citations
            for these papers do still contribute to the overall totals.
            This is useful, for example, if there are two ADS entries that
            really correspond to the same paper, and you want to hide one of
            them to avoid duplicates. Defaults to None.
        print_stats : bool, optional
            Whether to print statistics about the generated publication list.
            Defaults to True.
        n_authors : int, optional
            The maximum number of authors to display in the publication
            listings before truncating with "et al.". Note this also
            determines the auto-sorting of papers, as papers for which you
            are in the "et al." portion of the author list are automatically
            categorized as tertiary. The default is 4.
        tex_list_env : str, optional
            The LaTeX environment to use for the publication list.
            The default is "etaremune", but other common environments are
            "itemize" and "enumerate". Note that using "etaremune" requires
            adding "\\usepackage{etaremune}" to your LaTeX preamble.
        tex_file : str, optional
            The path to the output LaTeX file where the compiled publication
            list will be saved, by default "sections/publications.tex".
        """
        # Save params
        self.lib_code = lib_code
        self.library = Library(lib_code)

        self.name = name
        self.name_variations = name_variations

        # Merge config updates with defaults
        self.primary_config = {
            "title": "Primary Author:",
            "intro": None,
            "overrides": None,
        }
        self.primary_config |= {} if primary_config is None else primary_config

        self.secondary_config = {
            "title": "Co-Author with Major Contributions:",
            "intro": None,
            "overrides": None,
        }
        self.secondary_config |= {} if secondary_config is None else secondary_config

        self.tertiary_config = {
            "title": "Other Co-Author Papers:",
            "intro": None,
            "overrides": None,
        }
        self.tertiary_config |= {} if tertiary_config is None else tertiary_config

        self.hide = set() if hide is None else set(hide)

        # Save other params
        self.print_stats = print_stats
        self.n_authors = n_authors
        self.tex_list_env = tex_list_env
        self.tex_file = tex_file

    @staticmethod
    def _flag_collab(authors: list[str] | str) -> bool:
        """Flag if the paper is a collaboration paper."""
        if isinstance(authors, str):
            authors = [authors]
        return (
            authors[0].startswith("The")
            or "Observatory" in authors[0]
            or "Collaboration" in authors[0]
        )

    def _standardize_name(self, name: str) -> str:
        """Standardize a name to 'Last, F. M.' format."""
        # Don't try to standardize collaboration names, or those without commas
        if self._flag_collab(name):
            return name

        # Check if the name is in the variations list
        if self.name_variations is not None and name in self.name_variations:
            return self.name

        # Below we will split on commas. If name has no comma, skip.
        # Might need to do all this more robustly later
        if "," not in name:
            return name

        # Otherwise we have a regular name we want to standardize
        last, first = name.split(",")
        initials = " ".join([f"{item[0]}." for item in first.split()])
        return " ".join([last, initials])

    def _mangle_authors(self) -> None:
        """Mangle author lists to shorten and bold my name."""
        # Add "including..." when my name is not one of the first few authors
        including = f"including {self.name}"

        # Loop over papers and mangle author list
        for paper in self.papers:
            # If first author is a collaboration, keep only the first author
            if self._flag_collab(paper.author):
                paper.author = [paper.author[0], including]
                continue

            # Standardize names
            paper.author = [self._standardize_name(author) for author in paper.author]

            # If author list is already short, skip
            if len(paper.author) <= self.n_authors:
                continue

            # Keep first handful of authors
            if len(paper.author) > self.n_authors:
                paper.author = paper.author[: self.n_authors]

            # Is my name in the list?
            my_name = [name == self.name for name in paper.author]
            if sum(my_name) > 0:  # If my name is in list, just append et al.
                paper.author.append("et al.")
            else:  # Otherwise, drop last name, append et al. and including...
                paper.author = paper.author[:-1] + ["et al.", including]

    def retrieve_papers(self) -> None:
        """Retrieve papers from the ADS library."""
        if getattr(self, "papers", None) is None:
            self.papers = list(
                self.library.get_documents(
                    fl=[
                        "title",
                        "author",
                        "year",
                        "pub",
                        "page",
                        "volume",
                        "doi",
                        "bibcode",
                        "citation_count",
                        "pubdate",
                    ],
                )
            )
            self._mangle_authors()

    @property
    def n_papers(self) -> int:
        """Total number of papers."""
        self.retrieve_papers()
        return len(self.papers) - len(self.hide)

    @property
    def n_citations(self) -> int:
        """Total number of citations."""
        self.retrieve_papers()
        return sum(paper.citation_count for paper in self.papers)

    @property
    def h_index(self) -> int:
        """H-index."""
        self.retrieve_papers()

        # Get sorted list of citation counts (highest to lowest)
        cites = sorted([paper.citation_count for paper in self.papers], reverse=True)

        # Step through to calculate h-index
        h_index = 0
        for i, count in enumerate(cites):
            if count >= i + 1:
                h_index += 1
            else:
                break

        return h_index

    def sort_papers(self) -> tuple[list, list, list]:
        """Sort papers into primary, secondary, and tertiary lists."""
        self.retrieve_papers()
        papers_primary = []
        papers_secondary = []
        papers_tertiary = []

        # Get the overrides, and use empty sets if None
        primary_overrides = set(self.primary_config["overrides"] or [])
        secondary_overrides = set(self.secondary_config["overrides"] or [])
        tertiary_overrides = set(self.tertiary_config["overrides"] or [])

        for paper in self.papers:
            # First assign according to overrides
            if paper.doi is not None:
                if len(set(paper.doi) & primary_overrides) > 0:
                    papers_primary.append(paper)
                    continue
                elif len(set(paper.doi) & secondary_overrides) > 0:
                    papers_secondary.append(paper)
                    continue
                elif len(set(paper.doi) & tertiary_overrides) > 0:
                    papers_tertiary.append(paper)
                    continue
                elif len(set(paper.doi) & self.hide) > 0:
                    continue

            # If paper not in overrides, assign according to author list
            authors = paper.author
            is_me = [self.name in name for name in authors]
            if self._flag_collab(authors[0]) or is_me[-1]:
                papers_tertiary.append(paper)
            elif is_me[0]:
                papers_primary.append(paper)
            else:
                papers_secondary.append(paper)

        # Make sure they are sorted by publication date
        papers_primary.sort(key=lambda paper: paper.pubdate, reverse=True)
        papers_secondary.sort(key=lambda paper: paper.pubdate, reverse=True)
        papers_tertiary.sort(key=lambda paper: paper.pubdate, reverse=True)

        return papers_primary, papers_secondary, papers_tertiary

    @staticmethod
    def get_journal_abbrev(journal_name):
        """
        Convert a journal name to its AAS standard abbreviation.

        Args:
            journal_name (str): The full journal name to convert

        Returns:
            str: The AAS abbreviation if found, otherwise the original name
        """

        # Dictionary of journal names to AAS abbreviations
        # Based on AAS journal abbreviation standards
        journal_abbreviations = {
            # Major astronomy journals
            "astronomical journal": "AJ",
            "astrophysical journal": "ApJ",
            "astrophysical journal letters": "ApJL",
            "astrophysical journal supplement": "ApJS",
            "astrophysical journal supplement series": "ApJS",
            "astronomy and astrophysics": "A&A",
            "monthly notices of the royal astronomical society": "MNRAS",
            "publications of the astronomical society of the pacific": "PASP",
            "annual review of astronomy and astrophysics": "ARA&A",
            "astronomy and astrophysics review": "A&ARv",
            # Physical Review journals
            "physical review d": "PhRvD",
            "physical review letters": "PhRvL",
            "physical review": "PhRv",
            # Nature journals
            "nature": "Nature",
            "nature astronomy": "NatAs",
            "nature physics": "NatPh",
            # Science journals
            "science": "Science",
            "science advances": "SciA",
            # Solar and planetary science
            "solar physics": "SoPh",
            "icarus": "Icar",
            "planetary and space science": "P&SS",
            # Space science
            "space science reviews": "SSRv",
            "journal of geophysical research": "JGR",
            "geophysical research letters": "GeoRL",
            # Instrumentation
            "review of scientific instruments": "RScI",
            "publications of the astronomical society of australia": "PASA",
            # Conference proceedings
            "proceedings of the spie": "SPIE",
            "bulletin of the american astronomical society": "BAAS",
            # International journals
            "astronomy reports": "ARep",
            "astronomical and astrophysical transactions": "A&AT",
            "baltic astronomy": "BaltA",
            "chinese journal of astronomy and astrophysics": "ChJAA",
            "publications of the astronomical society of japan": "PASJ",
            # Specialized journals
            "living reviews in relativity": "LRR",
            "classical and quantum gravity": "CQGra",
            "general relativity and gravitation": "GReGr",
            "astrobiology": "AsBio",
            "astroparticle physics": "APh",
            "journal of cosmology and astroparticle physics": "JCAP",
            # Data journals
            "astronomy and computing": "A&C",
            "astronomical data analysis software and systems": "ADASS",
            # Preprint servers
            "arxiv e-prints": "arXiv",
            "arxiv": "arXiv",
            # Other
            "rubin observatory technical report": "Rubin Obs. Tech. Rep.",
            "nsf-doe vera c. rubin observatory technical report": "Rubin Obs. Tech. Rep.",
            "open journal of astrophysics": "OJAp",
        }

        # Standardize journal name (make lowercase; strip The, whitespace)
        standardized_name = journal_name.lower().removeprefix("the").strip()

        try:
            return journal_abbreviations[standardized_name]
        except KeyError:
            raise KeyError(f"No abbreviation found for journal {journal_name}")

    def _format_latex_entry(self, paper: Article) -> str:
        """Format article info for LaTeX."""
        # Start with title
        info = (
            "\\href{"
            f"https://ui.adsabs.harvard.edu/abs/{paper.bibcode}"
            "}{\\textit{"
            f"{paper.title[0]}"
            "}} \\\\ \n"
        )

        # Put my name in bold
        parts = ", ".join(paper.author).split(self.name)
        authors = parts[0] + f"\\textbf{{{self.name}}}" + parts[1]
        info += authors + f" ({paper.year})"

        # Now handle logic for journals
        pub = None if paper.pub is None else self.get_journal_abbrev(paper.pub)
        if pub is not None:
            info += " \n"
            if pub == "arXiv":
                info += f"{paper.page[0]} "
            else:
                info += f"{pub} "
                info += "" if paper.volume is None else f"{paper.volume} "
                info += (
                    ""
                    if (paper.volume is None or paper.page is None)
                    else f"{paper.page[0]} "
                )
        else:
            info += " "

        info += "\n\n"

        return info

    def _format_section(self, papers: list[Article], config: dict) -> str:
        """Format a section of the publication list."""
        if len(papers) == 0:
            return ""

        title = config["title"]
        intro = config["intro"] or ""
        if len(intro) > 0:
            intro = intro + "\n\n"

        output = f"\\textbf{{{title}}}\n\n"
        output += intro
        output += f"\\begin{{{self.tex_list_env}}}\n"
        for paper in papers:
            output += "\\item " + self._format_latex_entry(paper)
        output += f"\\end{{{self.tex_list_env}}}\n\n"

        return output

    def write_latex(self) -> None:
        """Write the publication lists in LaTeX format."""
        # Sort papers
        primary, secondary, tertiary = self.sort_papers()

        # Create latex string, appending papers for non-empty lists
        output = "\\section{Publications}\n\n"

        # Add summary stats
        if self.print_stats:
            now = datetime.now()
            output += (
                f"As of {now.strftime('%B %Y')}, "
                f"I have (co-)authored {self.n_papers} publications "
                f"with a total of {self.n_citations} citations "
                f"(\\textit{{h}}-index {self.h_index}). \\vspace{{2mm}}\n\n"
            )

        output += self._format_section(primary, self.primary_config)
        output += self._format_section(secondary, self.secondary_config)
        output += self._format_section(tertiary, self.tertiary_config)

        # Write to file
        with open(self.tex_file, "w") as file:
            file.write(output)


def main():

    LIB_CODE = "p11_8_nYTjuAD1LbKfZC5g"

    name = "Crenshaw J. F."
    name_variations = [
        "Crenshaw, John Franklin",
        "Crenshaw, John F.",
        "Crenshaw, J. F.",
        "Crenshaw, JF",
        "Crenshaw J. F.",
        "Crenshaw JF",
        "John Franklin Crenshaw",
        "John F. Crenshaw",
        "J. F. Crenshaw",
        "JF Crenshaw",
        "Crenshaw, John",
        "Crenshaw, J.",
        "Crenshaw, J",
        "Crenshaw J.",
        "Crenshaw J",
        "John Crenshaw",
        "J. Crenshaw",
        "J Crenshaw",
    ]

    primary_config = {
        "title": "First Author:",
        "intro": None,
        "overrides": None,
    }
    secondary_config = {
        "title": "Co-Author with Major Contributions:",
        "intro": None,
        "overrides": [
            "10.71929/RUBIN/2571480",  # DP1 photo-z technote
            "10.48550/arXiv.2505.02928",  # RAIL paper
            "10.48550/arXiv.2603.23786",  # DP1 paper
            "10.1093/mnras/stad302",  # SCOTCH paper (Lokken)
            "10.48550/arXiv.2601.10797",  # Crafford paper
        ],
    }
    tertiary_config = {
        "title": "Other Co-Author Papers:",
        "intro": (
            "The following include white papers and papers for which I was "
            "granted authorship due to more minor contributions, my role "
            "collecting or calibrating data, or my builder status within "
            "the Rubin Observatory and the Dark Energy Science Collaboration."
        ),
        "overrides": None,
    }
    hide = ["10.71929/RUBIN/2570536"]

    cvpb = CVPubBuilder(
        lib_code=LIB_CODE,
        name=name,
        name_variations=name_variations,
        primary_config=primary_config,
        secondary_config=secondary_config,
        tertiary_config=tertiary_config,
        hide=hide,
    )

    cvpb.write_latex()


if __name__ == "__main__":
    main()
