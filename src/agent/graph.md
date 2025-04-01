---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	planning_node(planning_node)
	map_section_generation(map_section_generation)
	collect_sections(collect_sections)
	write_roadmap_conclusion(write_roadmap_conclusion)
	compile_final_report(compile_final_report)
	__end__([<p>__end__</p>]):::last
	__start__ --> planning_node;
	compile_final_report --> __end__;
	generate_sections___end__ --> collect_sections;
	planning_node --> map_section_generation;
	write_roadmap_conclusion --> compile_final_report;
	collect_sections -.-> write_roadmap_conclusion;
	map_section_generation -.-> generate_sections_section_generate_query;
	subgraph generate_sections
	generate_sections_section_generate_query(section_generate_query)
	generate_sections_search_web_rag(search_web_rag)
	generate_sections_write_and_grade_section(write_and_grade_section)
	generate_sections___end__(<p>__end__</p>)
	generate_sections_search_web_rag --> generate_sections_write_and_grade_section;
	generate_sections_section_generate_query --> generate_sections_search_web_rag;
	generate_sections_write_and_grade_section -.-> generate_sections___end__;
	generate_sections_write_and_grade_section -.-> generate_sections_search_web_rag;
	end
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
