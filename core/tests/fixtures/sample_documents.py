from collections.abc import Callable

from tests.fixtures.contract_factory import (
    IMAGE_BLOCK,
    Borderless,
    SyntheticContract,
    SyntheticIdentifiers,
    dutch_lease,
    french_lease,
)

# Every person, company, address and number below is fictitious. Belgian numbers only have valid
# checksums; foreign IBANs are the standard documentation examples.
ids = SyntheticIdentifiers


def employment_contract_fr() -> SyntheticContract:
    niss = ids.national_number("900214", "158")
    enterprise = ids.enterprise_number("04581234")
    iban = ids.belgian_iban("0682345678")
    return SyntheticContract(
        filename="contrat-de-travail-fr.pdf",
        header="Brasserie Lambert & Fils SRL · Rue du Commerce 8, 4000 Liège",
        blocks=[
            "# CONTRAT DE TRAVAIL D'EMPLOYÉ À DURÉE INDÉTERMINÉE",
            "Entre :",
            "La société Brasserie Lambert & Fils SRL, dont le siège est établi Rue du Commerce 8, "
            f"4000 Liège, inscrite à la BCE sous le numéro {enterprise}, représentée par Monsieur "
            "Olivier Lambert, administrateur, ci-après dénommée « l'employeur »,",
            "Et :",
            "Madame Marie-Claire Dubois-Renard, née à Namur le 14 février 1990, numéro de registre "
            f"national {niss}, domiciliée Avenue des Tilleuls 23 bte 4, 5000 Namur, GSM 0478 55 12 34, "
            "e-mail mc.dubois@example.com, ci-après dénommée « le travailleur ».",
            "## Article 1 – Fonction",
            "Le travailleur est engagé en qualité de responsable administrative. Ses tâches comprennent "
            "notamment :",
            "- la gestion des commandes et de la facturation ;",
            "- le suivi des fournisseurs et des stocks ;",
            "- l'accueil téléphonique de la clientèle.",
            "## Article 2 – Rémunération",
            "La rémunération est composée des éléments suivants :",
            [
                ["Élément", "Montant"],
                ["Salaire mensuel brut", "3.200 euros"],
                ["Chèques-repas", "8 euros par jour presté"],
                ["Prime de fin d'année", "un treizième mois"],
            ],
            f"Le salaire est versé le dernier jour ouvrable du mois sur le compte {iban} du travailleur.",
            "## Article 3 – Horaire et lieu de travail",
            "L'horaire de travail est de 38 heures par semaine, du lundi au vendredi. Le travail est "
            "exécuté au siège de l'employeur.",
            "Fait à Liège, le 2 janvier 2026, en deux exemplaires.",
            Borderless([["Pour l'employeur, Olivier Lambert", "Le travailleur, Marie-Claire Dubois-Renard"]]),
        ],
        sensitive_values=[
            "Olivier Lambert",
            "Marie-Claire Dubois-Renard",
            "14 février 1990",
            niss,
            "Avenue des Tilleuls 23",
            "0478 55 12 34",
            "mc.dubois@example.com",
            iban,
            enterprise,
            "Rue du Commerce 8",
            "Brasserie Lambert",
        ],
        kept_values=["l'employeur", "le travailleur", "3.200 euros", "Madame", "2 janvier 2026"],
    )


def employment_contract_nl() -> SyntheticContract:
    # BIS number (foreign national): the birth month is increased by 40
    bis = ids.national_number("954610", "215")
    enterprise = ids.enterprise_number("08123456")
    iban = ids.belgian_iban("7350123456")
    return SyntheticContract(
        filename="arbeidsovereenkomst-nl.pdf",
        footer="Van Den Berg Logistics NV · Industrieweg 112, 2030 Antwerpen",
        blocks=[
            "# ARBEIDSOVEREENKOMST VOOR BEDIENDEN",
            "Tussen:",
            "Van Den Berg Logistics NV, met maatschappelijke zetel te Industrieweg 112, 2030 Antwerpen, "
            f"ondernemingsnummer {enterprise}, vertegenwoordigd door de heer Thomas Van Den Berg, "
            'gedelegeerd bestuurder, hierna "de werkgever",',
            "En:",
            "Mevrouw Lotte Vermeulen, geboren te Rotterdam op 10 juni 1995, BIS-nummer "
            f"{bis}, wonende Lange Lozanastraat 45, 2018 Antwerpen, gsm +32 485 67 89 01, e-mail "
            'lotte.vermeulen@example.org, hierna "de werknemer".',
            "## Artikel 1 – Functie",
            "De werknemer wordt aangeworven als planner. Haar taken omvatten onder meer:",
            "- het plannen van de dagelijkse ritten;",
            "- het opvolgen van de leveringen;",
            "- het contact met de klanten.",
            "## Artikel 2 – Loon",
            [
                ["Onderdeel", "Bedrag"],
                ["Bruto maandloon", "2.950 euro"],
                ["Maaltijdcheques", "8 euro per gewerkte dag"],
            ],
            f"Het loon wordt maandelijks gestort op rekening {iban} van de werknemer.",
            "## Artikel 3 – Duur",
            "De overeenkomst wordt gesloten voor onbepaalde duur en gaat in op 1 februari 2026.",
            "Opgemaakt te Antwerpen op 15 januari 2026 in twee exemplaren.",
            Borderless([["Voor de werkgever, T. Van Den Berg", "De werknemer, L. VERMEULEN"]]),
        ],
        sensitive_values=[
            "Thomas Van Den Berg",
            "Lotte Vermeulen",
            "VERMEULEN",
            "10 juni 1995",
            bis,
            "Lange Lozanastraat 45",
            "+32 485 67 89 01",
            "lotte.vermeulen@example.org",
            iban,
            enterprise,
            "Industrieweg 112",
        ],
        kept_values=["de werkgever", "de werknemer", "2.950 euro", "1 februari 2026"],
    )


def formal_notice_fr() -> SyntheticContract:
    enterprise = ids.enterprise_number("08876543")
    # Pre-IBAN account format, still found in older correspondence
    old_account = ids.id_card_number("0011234567")
    return SyntheticContract(
        filename="mise-en-demeure-fr.pdf",
        header="Cabinet Dupont · Avocats · Boulevard de Waterloo 34, 1000 Bruxelles · Tél. 02 511 22 33",
        blocks=[
            Borderless(
                [
                    [
                        "Maître Claire Dupont\nAvocate au barreau de Bruxelles\n"
                        "Boulevard de Waterloo 34\n1000 Bruxelles"
                    ]
                ]
            ),
            ">> Monsieur Kevin Janssens\nRue Haute 112\n1000 Bruxelles",
            ">> Bruxelles, le 14 octobre 2025",
            "## Concerne : mise en demeure – facture n° 2025-0412 impayée",
            "Monsieur,",
            "J'interviens en qualité de conseil de la société Print & Co SA, inscrite à la BCE sous le "
            f"numéro {enterprise}, qui m'a chargée de récupérer la somme de 2.450,00 euros restant due "
            "au titre de sa facture n° 2025-0412 du 3 juillet 2025, malgré deux rappels.",
            "Je vous mets en demeure de verser ce montant dans les quinze jours de la présente sur le "
            f"compte n° {old_account} de ma cliente. À défaut, ma cliente se réserve le droit de "
            "poursuivre le recouvrement par toutes voies de droit, sans autre avis.",
            "Veuillez agréer, Monsieur, l'expression de mes salutations distinguées.",
            ">> Claire Dupont",
        ],
        sensitive_values=[
            "Claire Dupont",
            "Kevin Janssens",
            "Rue Haute 112",
            "Boulevard de Waterloo 34",
            "02 511 22 33",
            old_account,
            enterprise,
            "Print & Co",
        ],
        kept_values=["2.450,00 euros", "2025-0412", "14 octobre 2025", "Maître", "Monsieur"],
    )


def power_of_attorney_fr() -> SyntheticContract:
    niss = ids.national_number("620303", "081")
    card_marc = ids.id_card_number("5912345678")
    card_anne = ids.id_card_number("5923456789")
    iban = ids.belgian_iban("0634567890")
    return SyntheticContract(
        filename="procuration-fr.pdf",
        blocks=[
            "# PROCURATION",
            "Je soussigné, Monsieur Marc Leclercq, né à Charleroi le 3 mars 1962, numéro de registre "
            f"national {niss}, titulaire de la carte d'identité n° {card_marc}, domicilié Rue de la "
            "Station 7, 6000 Charleroi, ci-après « le mandant »,",
            "donne par la présente procuration à Madame Anne Leclercq, née le 21 novembre 1965, "
            f"titulaire de la carte d'identité n° {card_anne}, domiciliée à la même adresse, "
            "ci-après « le mandataire »,",
            "afin d'accomplir en son nom les actes suivants :",
            "- vendre le véhicule immatriculé 1-KLM-456 et en percevoir le prix ;",
            f"- effectuer toute opération sur le compte {iban} ;",
            "- signer tout document nécessaire à ces opérations.",
            "La présente procuration est valable jusqu'au 31 décembre 2026.",
            "Fait à Charleroi, le 5 novembre 2025.",
            Borderless([["Le mandant, M. Leclercq", "Le mandataire, A. Leclercq"]]),
        ],
        sensitive_values=[
            "Marc Leclercq",
            "Anne Leclercq",
            "3 mars 1962",
            "21 novembre 1965",
            niss,
            card_marc,
            card_anne,
            "Rue de la Station 7",
            iban,
            "1-KLM-456",
        ],
        kept_values=["le mandant", "le mandataire", "31 décembre 2026"],
    )


def vehicle_sale_nl() -> SyntheticContract:
    return SyntheticContract(
        filename="verkoop-voertuig-nl.pdf",
        blocks=[
            "# VERKOOPOVEREENKOMST TWEEDEHANDSVOERTUIG",
            "Tussen de verkoper:",
            "Sofie De Clercq, wonende Brugsesteenweg 250, 8500 Kortrijk, gsm 0496 12 34 56,",
            "en de koper:",
            "Mark de Vries, wonende Keizersgracht 15, 1015 Amsterdam (Nederland), telefoon +31 6 12345678,",
            "wordt het volgende voertuig verkocht:",
            [
                ["Merk en model", "Volkswagen Golf"],
                ["Nummerplaat", "2-XYZ-987"],
                ["Eerste inschrijving", "12 maart 2019"],
                ["Kilometerstand", "84.300 km"],
                ["Prijs", "12.500 euro"],
            ],
            "De prijs wordt betaald door overschrijving vanaf rekening NL91 ABNA 0417 1643 00 van de "
            "koper, uiterlijk bij de levering van het voertuig.",
            "Het voertuig wordt verkocht in de staat waarin het zich bevindt, zoals bezichtigd en "
            "proefgereden door de koper.",
            "Opgemaakt te Kortrijk op 8 november 2025.",
            Borderless([["De verkoper", "De koper"], ["Sofie De Clercq", "Mark de Vries"]]),
        ],
        sensitive_values=[
            "Sofie De Clercq",
            "Mark de Vries",
            "Brugsesteenweg 250",
            "Keizersgracht 15",
            "0496 12 34 56",
            "+31 6 12345678",
            "NL91 ABNA 0417 1643 00",
            "2-XYZ-987",
        ],
        kept_values=["de verkoper", "de koper", "12.500 euro", "Volkswagen Golf"],
    )


def invoice_fr() -> SyntheticContract:
    supplier_vat = ids.enterprise_number("06543210")
    client_vat = ids.enterprise_number("04321098")
    iban = ids.belgian_iban("3101234567")
    return SyntheticContract(
        filename="facture-fr.pdf",
        footer=f"Atelier Graphique Mertens SRL · TVA {supplier_vat} · IBAN {iban}",
        blocks=[
            IMAGE_BLOCK,
            "Atelier Graphique Mertens SRL\nChaussée de Louvain 410, 1030 Schaerbeek\n"
            f"TVA {supplier_vat}\nTél. 02 245 67 89 · facturation@mertens-graphique.be",
            ">> Hôtel du Lac SA\nÀ l'attention de Madame Isabelle Laurent\nPlace du Marché 3\n"
            f"6700 Arlon\nTVA {client_vat}",
            "# FACTURE N° F-2025-0187",
            "Date de facture : 31 octobre 2025 · Échéance : 30 novembre 2025",
            [
                ["Description", "Quantité", "Prix unitaire", "Total HTVA"],
                ["Conception de la carte des menus", "1", "850,00 €", "850,00 €"],
                ["Impression des cartes (format A4)", "200", "1,20 €", "240,00 €"],
                ["Livraison", "1", "35,00 €", "35,00 €"],
            ],
            [
                ["Total HTVA", "1.125,00 €"],
                ["TVA 21 %", "236,25 €"],
                ["Total TVAC", "1.361,25 €"],
            ],
            f"Merci de verser le montant total sur le compte {iban} avant le 30 novembre 2025, avec la "
            "communication structurée +++123/4567/89012+++.",
        ],
        sensitive_values=[
            "Isabelle Laurent",
            "Chaussée de Louvain 410",
            "Place du Marché 3",
            supplier_vat,
            client_vat,
            "02 245 67 89",
            "facturation@mertens-graphique.be",
            iban,
            "Atelier Graphique Mertens",
            "Hôtel du Lac",
        ],
        kept_values=["F-2025-0187", "1.361,25 €", "+++123/4567/89012+++", "Madame"],
    )


def data_processing_agreement_en() -> SyntheticContract:
    enterprise = ids.enterprise_number("07654321")
    return SyntheticContract(
        filename="data-processing-agreement-en.pdf",
        blocks=[
            "# DATA PROCESSING AGREEMENT",
            "This agreement is entered into between:",
            f"CloudNest BV, registered under enterprise number {enterprise}, with registered office at "
            "Rue de la Science 14, 1040 Brussels, represented by Mr Pieter Claes, CEO "
            '(hereinafter "the Processor"),',
            "and",
            "Harbour Analytics Ltd, 12 Baker Street, London NW1 6XE, United Kingdom, represented by "
            "Ms Sarah O'Connor, Data Protection Officer, sarah.oconnor@example.co.uk, "
            '+44 20 7946 0958 (hereinafter "the Controller").',
            "## 1. Subject matter",
            "The Processor processes personal data on behalf of the Controller for the provision of "
            "cloud hosting services. The following categories of data are processed:",
            "- identification and contact data of the Controller's customers;",
            "- order and invoicing data;",
            "- technical logs.",
            "## 2. Sub-processors",
            "The Controller authorises the following sub-processors:",
            [
                ["Sub-processor", "Location", "Service"],
                ["DataVault SAS", "Paris, France", "Backup storage"],
                ["MailRelay GmbH", "Frankfurt, Germany", "E-mail delivery"],
            ],
            "## 3. Fees",
            "The services are invoiced 1,200 EUR per year, payable to account GB82 WEST 1234 5698 7654 32.",
            "Signed in Brussels on 20 October 2025.",
            Borderless([["For the Processor, Pieter Claes", "For the Controller, Sarah O'Connor"]]),
        ],
        sensitive_values=[
            "Pieter Claes",
            "Sarah O'Connor",
            "Rue de la Science 14",
            "12 Baker Street",
            "sarah.oconnor@example.co.uk",
            "+44 20 7946 0958",
            "GB82 WEST 1234 5698 7654 32",
            enterprise,
            "CloudNest",
            "Harbour Analytics",
        ],
        kept_values=["the Processor", "the Controller", "1,200 EUR", "20 October 2025"],
    )


def lease_de() -> SyntheticContract:
    niss = ids.national_number("700512", "047")
    iban = ids.belgian_iban("0012345678")
    return SyntheticContract(
        filename="mietvertrag-de.pdf",
        blocks=[
            "# MIETVERTRAG FÜR EINE HAUPTWOHNUNG",
            "Zwischen",
            "Herrn Klaus Schmitz, geboren am 12.05.1970 in Eupen, Nationalregisternummer "
            f"{niss}, wohnhaft Klötzerbahn 5, 4700 Eupen, Telefon 087 55 44 33, E-Mail "
            'k.schmitz@example.be, nachstehend "der Vermieter" genannt,',
            "und",
            "Frau Julia Kessler, geboren am 3. August 1988, wohnhaft Bergstraße 21, 4730 Raeren, "
            'nachstehend "die Mieterin" genannt,',
            "wird folgender Vertrag geschlossen:",
            "## Artikel 1 – Mietgegenstand",
            "Der Vermieter vermietet der Mieterin eine Wohnung im zweiten Stock des Gebäudes "
            "Kirchstraße 12, 4700 Eupen, bestehend aus zwei Zimmern, einer Küche und einem Badezimmer.",
            "## Artikel 2 – Miete",
            f"Die monatliche Miete beträgt 780 Euro und ist bis zum 5. jedes Monats auf das Konto {iban} "
            "des Vermieters zu überweisen.",
            "## Artikel 3 – Dauer",
            "Der Vertrag beginnt am 1. Dezember 2025 und wird für eine Dauer von drei Jahren geschlossen.",
            "Eupen, den 10. November 2025",
            Borderless([["Der Vermieter, Klaus Schmitz", "Die Mieterin, Julia Kessler"]]),
        ],
        sensitive_values=[
            "Klaus Schmitz",
            "Julia Kessler",
            "12.05.1970",
            "3. August 1988",
            niss,
            "Klötzerbahn 5",
            "Bergstraße 21",
            "Kirchstraße 12",
            "087 55 44 33",
            "k.schmitz@example.be",
            iban,
        ],
        kept_values=["der Vermieter", "die Mieterin", "780 Euro", "1. Dezember 2025"],
    )


SAMPLE_DOCUMENTS: list[Callable[[], SyntheticContract]] = [
    french_lease,
    dutch_lease,
    employment_contract_fr,
    employment_contract_nl,
    formal_notice_fr,
    power_of_attorney_fr,
    vehicle_sale_nl,
    invoice_fr,
    data_processing_agreement_en,
    lease_de,
]
