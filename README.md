# GEL-MaxSAT

![license MIT](https://img.shields.io/github/license/andrewijano/gel-max-sat)
> A tractable Graphic EL MaxSAT solver

## Install the dependencies

```bash
pip3 install -r requirements.txt
```


## Input format

The input is an ontology in OWL format. This ontology can only contain axioms in the following form, where `C`, `D` are *basic concepts*, `r`, `s`, `t` are *roles* and `a`, `b` are *individuals*:

- `C ⊑ D`
- `C ⊑ ∃r.D`
- `C ≡ D`
- `C ≡ ∃r.D`
- `C(a)`
- `r(a, b)`
- `r ⊑ s`
- `r ∘ s ⊑ t`

Due to technical limitations, axioms of the form `∃r.C ⊑ D` need to be represented as `"∃r.C" ≡ ∃r.C` and `"∃r.C" ⊑ D`. 


Add a `rdfs:comment` to every uncertain axiom. There **must** be the header `#! pbox-id` in these comments, followed, in the next line, for its unique `id`.

> ### For example: 
> 
> Supose some axiom `Ax0` is uncertain. 
> You need to add one `rdfs:comment`s to this, with the content  
> ```
> #! pbox-id
> 0 
> ```

## Usage

The `<inputfile>` will be your OWL file with probabilistic restrictions.

```bash
python3 gel_max_sat.py <inputfile>
```

## Experiments

The experiments (with the default values) can be made by running

```bash
python3 experiments.py [optional arguments]
```

### Generation of random formulas

The formulas in the experiments are generated randomly. Because every Graphic EL knowledge base can be represented as a directed graph, the problem of generating a random GEL knowledge base can be reduced to the problem of generating a random graph. This process is done as follows.

We have the following fixed values:

- `n`, the number of concepts;
- `m`, the number of axioms;
- `p`, the number of finite weighted axioms;
- `r`, the number of roles.

First, we start with a graph `G` with zero arrows and three vertices: `⊤` (the *top concept*), `⊥` (the *bottom concept*) and `init` (the artificial initial concept). Then, we add `n` vertices and `r` roles to `G`. After that, we add `m - p` infinite weighted arrows and `p` finite weighted arrows. The arrows are added by chosing randomly two vertices `C` and `D` (`n + 3` possibilities for each one) and creating an arrow from `C` to `D`, its role is chosen uniformly between an "is a" role (`C ⊑ D`) and the `r` other roles (`C ⊑ ∃ri.D`).  

Note that we do not need to generate body-existential axioms (`∃ri.C ⊑  D`) because they can be represented by simple and existential-head axioms. Also, individual concepts are represented by every concept `C` such that `init ⊑ C`.

Finally, during and after the insertion of arrows, the graph is completed following the graph completion rules.

### Plotting

The experiments can be plotted by running

```bash
python3 plot.py [optional arguments] data/experiments/<experiment>
```

### Example

This is the plot of an experiment using default configuration:

![Plot using default configuration](./data/plots/m11-M200-s1-n60-p10-t100-r3.png)

## License

[MIT](https://choosealicense.com/licenses/mit/)
