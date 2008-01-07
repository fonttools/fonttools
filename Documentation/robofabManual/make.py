import bonbon.builder
import os

root = os.path.dirname(__file__)
builder = bonbon.builder.SiteBuilder(root)

builder.build()

