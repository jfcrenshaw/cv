"""Script to generate CV publication list from ADS library."""

from ads.libraries import Library
from ads.search import Article
from datetime import datetime


class CVPubBuilder:
    """Class to generate CV publication lists from ADS library."""

    def __init__(
        self,
        lib_code: str,
        name: str,
        name_variations: list[str] | None = None,
        doi_overrides: dict[str, set[str]] | None = None,
        n_authors: int = 4,
        tex_file: str = "sections/publications.tex",
    ) -> None:
        """Initialize the CVPubBuilder.

        Parameters:
        -----------
        lib_code : str
            The ADS library code to retrieve papers from.
        name : str
            The standardized name to bold in author lists.
        name_variations : list of str, optional
            List of name variations to standardize to `name`.
            Default is None.
        doi_overrides : dict of str to set of str, optional
            Dictionary with keys 'primary', 'secondary', 'tertiary' mapping to
            sets of DOIs to override automatic sorting into publication
            categories. Default is None.
        n_authors : int, optional
            Number of authors to show before truncating with "et al."
            Default is 4.
        tex_file : str, optional
            Path to the output LaTeX file.
            Default is 'sections/publications.tex'.
        """
        # Save params
        self.lib_code = lib_code
        self.name = name
        self.name_variations = name_variations
        self.library = Library(lib_code)
        self.doi_overrides = doi_overrides
        self.n_authors = n_authors
        self.tex_file = tex_file

    @staticmethod
    def _flag_collab(authors: list[str] | str) -> bool:
        """Flag if the paper is a collaboration paper."""
        if isinstance(authors, str):
            authors = [authors]
        return authors[0].startswith("The")

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
        return len(self.papers)

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

        for paper in self.papers:
            # First assign according to overrides
            if self.doi_overrides is not None:
                if len(set(paper.doi) & self.doi_overrides["primary"]) > 0:
                    papers_primary.append(paper)
                    continue
                elif len(set(paper.doi) & self.doi_overrides["secondary"]) > 0:
                    papers_secondary.append(paper)
                    continue
                elif len(set(paper.doi) & self.doi_overrides["tertiary"]) > 0:
                    papers_tertiary.append(paper)
                    continue

            # If paper not in overrides, assign according to author list
            authors = paper.author
            if self._flag_collab(authors[0]):
                papers_tertiary.append(paper)
            elif authors[0] == self.name or authors[1] == self.name:
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

        Parameters:
        -----------
        journal_name : str
            The full journal name to convert.

        Returns:
        --------
        str
            The AAS abbreviation if found, otherwise the original name
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
        }

        # Standardize journal name (make lowercase; strip The, whitespace)
        standardized_name = journal_name.lower().strip("the").strip()

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
            if pub != "arXiv":
                info += f"{pub} "
            info += "" if paper.volume is None else f"{paper.volume} "
            info += "" if paper.page is None else f"{paper.page[0]} "
        else:
            info += " "

        # Append link to ADS
        # info += f"\\ADS{{https://ui.adsabs.harvard.edu/abs/{paper.bibcode}}}"

        info += "\n\n"

        return info

    def print_latex(self) -> None:
        """Print the publication lists in LaTeX format.

        Note the output is saved in self.tex_file.
        """
        # Sort papers
        primary, secondary, tertiary = self.sort_papers()

        # Create latex string, appending papers for non-empty lists
        output = "\\section{Publications}\n\n"

        # Add summary stats
        now = datetime.now()
        output += (
            f"As of {now.strftime('%B %Y')}, I have (co-)authored {self.n_papers} "
            f"papers, with a total of {self.n_citations} citations "
            f"and an h-index of {self.h_index}. \\vspace{{2mm}}\n\n"
        )

        if len(primary) > 0:
            output += "\\textbf{First and Second Author:}\n"
            output += "\\begin{etaremune}\n"
            for paper in primary:
                output += "\\item " + self._format_latex_entry(paper)
            output += "\\end{etaremune}\n\n"

        if len(secondary) > 0:
            output += "\\textbf{Co-Author with Major Contributions:}\n"
            output += "\\begin{etaremune}\n"
            for paper in secondary:
                output += "\\item " + self._format_latex_entry(paper)
            output += "\\end{etaremune}\n\n"
            output += "\n\n"

        if len(tertiary):
            output += "\\textbf{Other Co-Author Papers:}\n"
            output += "\\begin{etaremune}\n"
            for paper in tertiary:
                output += "\\item " + self._format_latex_entry(paper)
            output += "\\end{etaremune}\n\n"

        # Write to file
        with open(self.tex_file, "w") as file:
            file.write(output)


def main():
    # Library code for my personal ADS library
    LIB_CODE = "p11_8_nYTjuAD1LbKfZC5g"

    # Name I want printed in CV entries
    name = "Crenshaw J. F."
    # Variations of my name to standardize to the above
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

    # DOIs to override automatic sorting into primary, secondary, tertiary
    doi_overrides = {
        "primary": set(),
        "secondary": set(
            [
                "10.71929/RUBIN/2571480",  # DP1 photo-z technote
                "10.48550/arXiv.2505.02928",  # RAIL paper
            ]
        ),
        "tertiary": set(),
    }

    # Create the CVPubBuilder
    cvpb = CVPubBuilder(
        lib_code=LIB_CODE,
        name=name,
        name_variations=name_variations,
        doi_overrides=doi_overrides,
        n_authors=4,
        tex_file="sections/publications.tex",
    )

    # Print the LaTeX file
    cvpb.print_latex()


if __name__ == "__main__":
    main()
